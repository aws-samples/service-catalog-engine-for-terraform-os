#!/bin/bash
set -e

BOOTSTRAP_STACK_NAME=Bootstrap-TRE
TEMPLATE_BODY='file://cfn-templates/Bootstrap.yaml'

validate_aws_command_result() {
  # Pass the output of an aws command as $1.
  # If $1 is not valid json, assume it is an error returned from the aws command.
  if [[ ! `echo $1 | jq .` ]]
  then
    echo $1
    exit
  fi
}

get_stack_status() {
  STACK_STATUS=$(aws cloudformation describe-stacks --stack-name $BOOTSTRAP_STACK_NAME --region $AWS_REGION --query Stacks[0].StackStatus)
}

check_stack_operation_result() {
  echo "Checking stack status: $STACK_STATUS"
  if [[ "$STACK_STATUS" =~ CREATE_COMPLETE|UPDATE_COMPLETE ]]
  then
    echo "The stack operation succeeded."
  else
    echo "The stack operation failed."
    exit 1
  fi
}

await_finished_stack_status() {
  echo "Waiting for the stack operation to finish."
  while [[ -z "$STACK_STATUS" || "$STACK_STATUS" =~ IN_PROGRESS ]]
  do
    sleep 5
    get_stack_status
    echo "Stack status: $STACK_STATUS"
  done
  check_stack_operation_result
}


echo "Looking for the bootstrap bucket stack, using name $BOOTSTRAP_STACK_NAME"
STACK_EXISTS_CHECK=`aws cloudformation describe-stacks --stack-name $BOOTSTRAP_STACK_NAME --region $AWS_REGION 2>&1 || true`

if [[ "$STACK_EXISTS_CHECK" =~ "does not exist" ]]
then

  echo "Did not find the bootstrap bucket stack. Creating it."
  STACK_CREATE_RESULT=`aws cloudformation create-stack --stack-name $BOOTSTRAP_STACK_NAME --template-body $TEMPLATE_BODY --capabilities CAPABILITY_NAMED_IAM --region $AWS_REGION 2>&1 || true`
  validate_aws_command_result "$STACK_CREATE_RESULT"
  await_finished_stack_status

else

  # Make sure the last describe-stacks command succeeded.
  validate_aws_command_result "$STACK_EXISTS_CHECK"

  echo "Found the bootstrap bucket stack. Checking for updates."

  STACK_UPDATE_RESULT=`aws cloudformation update-stack --stack-name $BOOTSTRAP_STACK_NAME --template-body $TEMPLATE_BODY --capabilities CAPABILITY_NAMED_IAM --region $AWS_REGION 2>&1 || true`

  if [[ "$STACK_UPDATE_RESULT" =~ "No updates are to be performed" ]]
  then
    echo "No updates are to be performed."
  else
    validate_aws_command_result "$STACK_UPDATE_RESULT"
    await_finished_stack_status
  fi

fi
