# CI/CD AWS

Create a new project with a CI/CD pipeline using CodeCommit & CodeBuild (AWS).


### Architecture 


![CI/CD Pipeline](doc/architecture.png)



### CI/CD workflow

1. Keep your code in a git repository (Codecommit)
2. On git push event, a lambda function is triggered. It keeps track of the build number and environment (git branch). The last commit is stored into SSM, then a CodeBuild job is triggered (app.py).
3. The CodeBuild job is a python script deploying your infrastructure and your code. The deployment package is saved on S3.


### Setup 

In `init.py`, replace the variable `PROJECT_NAME` by the name of your project (line 18).

Then, run the following command: 

```
python init.py
```

It will create the minimum resources: AWS CodeCommit, CodeBuild, Lambda and S3 bucket (3 Cloudformation stacks). Make sure you have the IAM permissions to set-up these resources.

If you just want to update the codebuild job, run:

```
python init.py --codebuild-job
```

!! By default, the role attached to your codebuild job has full access to your AWS account in order to create any kind of resources. Depending on your use case, you may want to restrict the permissions. !!


### Codebuild job

You can customize the codebuild job depending on your need (run.py). In this example, the run.py deploy:
- A static website
- A lambda function

If you need more advanced customization, you can modify the cloudformation template to pre-install other libraries. 

As mentioned above, the codebuild job has full-access to your AWS account. If you want, you can restrict the IAM permissions in the project.yaml. 


### Architecture as a code

Clone the codecommit repository that has been created and copy the folders:
- application
- platform

The codebuild job uses an environment variable to indicate the location of a deployspec (platform/deployspec.yaml). Use this file to create stack (create_stack) or delete (delete_stack) cloudformation stacks. The template path is the original cloudformation template.

The pipeline will automatically update the stack if it has already been deployed once. 

Use the teardown codebuild job to teardown an existing stack.


### Multiple environments

Use the branch name to create different resource names. For example, append `-${Branch}` at the end of your lambda function to differenciate DEV & PROD environment, assuming that master branch would be the PROD branch.
