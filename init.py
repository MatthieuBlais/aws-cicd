import yaml
import boto3
import zipfile
import logging
import time 
import sys

logger = logging.getLogger()
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

#
#	PROJECT NAME CONSTANT: TO REPLACE
#
PROJECT_NAME="myproject"


region = 'ap-southeast-1'

cloudformation = boto3.client('cloudformation', region_name=region)
s3 = boto3.client('s3', region_name=region)

def set_project_name(project_name, filename):
	try:
		deployspec = open(filename, "r").read()
		deployspec = deployspec.replace("{PROJECT_NAME}", project_name)
		with open(filename, "w+") as f:
			f.write(deployspec)
	except Exception as e:
		raise


def load_deployspec(filename):
	try:
		return yaml.load(open(filename, "r"))
	except Exception as e:
		raise

def read(filename, mode="r"):
	try:
		return open(filename, mode).read()
	except Exception as e:
		raise

def create_stack(config):
	cloudformation.create_stack(
		StackName=config["StackName"],
		TemplateBody=read(config["TemplateName"]),
		Capabilities=[
		    'CAPABILITY_IAM', 'CAPABILITY_NAMED_IAM'
		],
		Parameters=[ {
            'ParameterKey': key,
            'ParameterValue': config["Properties"][key]
        } for key in config["Properties"].keys()])

def describe_stack(stack_name):
	try:
		response = cloudformation.describe_stacks(
		    StackName=stack_name
		)
		status = response["Stacks"][0]["StackStatus"]
		return status
	except Exception as e:
		raise

def wait_for_stack(stack_name):
	status = describe_stack(stack_name)
	while status == "CREATE_IN_PROGRESS":
		logging.info("-> CREATE_IN_PROGRESS")
		time.sleep(30)
		status = describe_stack(stack_name)
	logging.info("=> DONE: {}".format(status))
	return status

def upload(filename, bucket, key):
	s3.put_object(Bucket=bucket, Key=key, Body=read(filename, "rb"))

def main(project_name, full_init=True):
	set_project_name(project_name, "deployspec.yaml")
	logging.info("LOADING TEMPLATES...")
	stacks = load_deployspec("deployspec.yaml")

	if full_init:
		## CREATE APPLICATION BUCKET
		logging.info("CREATE APPLICATION BUCKET STACK")
		create_stack(stacks[0])
		wait_for_stack(stacks[0]["StackName"])

		## UPLOAD LAMBDA CODE
		logging.info("UPLOADING LAMBDA CODECOMMIT TRIGGER CODE")
		zipfile.ZipFile('automation.zip', mode='w').write("app.py")
		upload('automation.zip', stacks[1]["Properties"]["AppBucket"], stacks[1]["Properties"]["CodeS3Key"])

		# ## CREATE LAMBDA CODECOMMIT
		logging.info("CREATING LAMBDA CODECOMMIT TRIGGER")
		create_stack(stacks[1])
		wait_for_stack(stacks[1]["StackName"])

		# ## CREATE CODECOMMIT
		logging.info("CREATING CODECOMMIT REPO, TRIGGER AND CODEBUILD")
		create_stack(stacks[2])
		wait_for_stack(stacks[2]["StackName"])

	# ## UPLOAD RUN.SH
	logging.info("UPLOADING CODEBUILD JOB")
	zipfile.ZipFile('run.zip', mode='w').write("run.py")
	upload('run.py', stacks[2]["Properties"]["AppBucket"], stacks[2]["Properties"]["RunKey"])
	upload('run.zip', stacks[2]["Properties"]["AppBucket"], stacks[2]["Properties"]["RunZipKey"])

if __name__ == '__main__':
	full_init = True
	if len(sys.argv) > 1:
		if sys.argv[1] == "--codebuild-job":
			full_init=False
	main(PROJECT_NAME, full_init)
