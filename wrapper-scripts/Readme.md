## Building the Instance Script

This directory contains the Python module that is downloaded, installed, and executed on the EC2 instances. It is a wrapper around the Terraform CLI.

To build the module from this directory:

* pip3 install wheel (one-time setup)
* python3 setup.py bdist_wheel

Then sync it to this S3 bucket:

* aws s3 sync dist s3://terraform-engine-bootstrap-<your_account_id>-\<region>/dist

Every time a new instance starts, it will download the terraform_runner module from this bucket and install it. 


## Unit Tests

To run the unit tests, execute this command from this directory:

* python3 -m unittest
