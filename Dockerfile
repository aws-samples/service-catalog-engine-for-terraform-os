FROM python:3.9-slim-buster

# Install Curl, unzip and groff for aws-cli
RUN apt-get update && apt-get install curl unzip groff less git jq -y && apt-get clean autoclean && apt-get autoremove --yes

# Set up GoLang
COPY --from=golang:1.20-buster /usr/local/go/ /usr/local/go/
ENV PATH="/usr/local/go/bin:${PATH}"

# Install AWS CLI and Cleanup
RUN curl "https://awscli.amazonaws.com/awscli-exe-linux-$(uname -m).zip" -o "/tmp/awscliv2.zip" && unzip /tmp/awscliv2.zip -d /tmp/ && /tmp/aws/install && rm -rf /tmp/aws*
RUN aws --version

# Install SAM-CLI
RUN pip --no-cache-dir install aws-sam-cli && sam --version

# Set work-directory and entrypoint
RUN mkdir /tre
WORKDIR /tre
CMD []
ENTRYPOINT ["/bin/bash"]