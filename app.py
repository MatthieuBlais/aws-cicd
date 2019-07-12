import os
import logging
import boto3
import json
from datetime import datetime


logger = logging.getLogger()
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)


def handler(event, context):
	logging.info('handler event: {}'.format(json.dumps(event)))

	region = os.environ["REGION"]
	application = os.environ["APPLICATION"]

	record = event["Records"][0]
	branch = record['codecommit']['references'][0]['ref'].split("/")[-1]

	logging.info('branch: {}'.format(branch))


	ssm = boto3.client("ssm", region_name=region)
	parameter = "/{}/{}/build".format(application, branch)
	try:
		last_commit = ssm.get_parameter(Name=parameter)["Parameter"]["Value"]
		if last_commit == record['codecommit']['references'][0]["commit"]:
			return False
	except Exception:
		pass

	response = ssm.put_parameter(Name=parameter, Value=record['codecommit']['references'][0]["commit"], Type='String', Overwrite=True)
	logging.info('ssm response: {}'.format(json.dumps(response)))
	build = response["Version"]

	env = [
		{ 'name': "BRANCH", 'value': branch} ,
		{'name': "BUILD_NUMBER", 'value': str(build) }
	]
	codebuild = boto3.client("codebuild", region_name=region)

	response = codebuild.start_build(
		projectName=application,
		sourceVersion=branch,
		environmentVariablesOverride=env
		)

	return True