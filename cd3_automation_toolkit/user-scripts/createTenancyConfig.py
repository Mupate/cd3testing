#!/usr/bin/python3
# Copyright (c) 2016, 2019, Oracle and/or its affiliates. All rights reserved.
#
# This script will help in initializing the docker container; creates config and variables files.
#
# Author: Shruthi Subramanian
#

import argparse
import logging
import os
import re
import shutil
import sys
import datetime
import configparser
import distutils
from distutils import dir_util
import oci
from oci.object_storage import ObjectStorageClient
import git
import glob
import yaml
sys.path.append(os.getcwd()+"/..")
from commonTools import *
from copy import deepcopy

def paginate(operation, *args, **kwargs):
    while True:
        response = operation(*args, **kwargs)
        for value in response.data:
            yield value
        kwargs["page"] = response.next_page
        if not response.has_next_page:
            break

def create_devops_resources(config,signer):

    # Check existence of Topic
    toolkit_topic_id = ''
    resource_search = oci.resource_search.ResourceSearchClient(config, retry_strategy=oci.retry.DEFAULT_RETRY_STRATEGY,signer=signer)
    ons_query = 'query onstopic resources where displayname = \''+topic_name+'\''
    ons_search_details = oci.resource_search.models.StructuredSearchDetails(type='Structured',
                                                                            query=ons_query)
    ons_resources = oci.pagination.list_call_get_all_results(resource_search.search_resources, ons_search_details,
                                                             limit=1000)
    for ons in ons_resources.data:
        topic_state = ons.lifecycle_state
        if topic_state != 'ACTIVE':
            print("Topic exists with name(" + topic_name + ") but is not in ACTIVE state. Exiting...")
            exit(1)
        toolkit_topic_id = ons.identifier
        topic_comp = ons.compartment_id
        print("Topic exists with name(" + topic_name + ") in compartment '"+topic_comp+"' Reusing same.")

    # Create New Topic
    if toolkit_topic_id=='':
        # Initialize ONS service client with default config file
        ons_client = oci.ons.NotificationControlPlaneClient(config=config,
                                                            retry_strategy=oci.retry.DEFAULT_RETRY_STRATEGY,
                                                            signer=signer)

        create_topic_response = ons_client.create_topic(create_topic_details=oci.ons.models.CreateTopicDetails(
                name=topic_name, compartment_id=compartment_ocid, description="Created by Automation ToolKit")).data
        toolkit_topic_id = create_topic_response.topic_id



    # Check existence of DevOps Project
    toolkit_project_id = ''
    devops_query = 'query devopsproject resources where displayname = \'' + project_name + '\''
    devops_search_details = oci.resource_search.models.StructuredSearchDetails(type='Structured',
                                                                               query=devops_query)
    devops_resources = oci.pagination.list_call_get_all_results(resource_search.search_resources, devops_search_details,
                                                                limit=1000)
    for project in devops_resources.data:
        project_state = project.lifecycle_state
        if project_state != 'ACTIVE':
            print("Project exists with name(" + project_name + ") but is not in ACTIVE state. Exiting...")
            exit(1)
        toolkit_project_id = project.identifier
        project_comp = project.compartment_id
        print("Project exists with name(" + project_name + ") in compartment '"+project_comp+"' Reusing same.")

    # Initialize Devops service client with default config file
    devops_client = oci.devops.DevopsClient(config=config, retry_strategy=oci.retry.DEFAULT_RETRY_STRATEGY,
                                                signer=signer)
    # Create Devops Project
    if toolkit_project_id=='':
        create_project_response = devops_client.create_project(
            create_project_details=oci.devops.models.CreateProjectDetails(
                name=project_name,
                notification_config=oci.devops.models.NotificationConfig(
                    topic_id=toolkit_topic_id),
                compartment_id=compartment_ocid,
                description="Created by Automation ToolKit")).data

        toolkit_project_id = create_project_response.id
    # Check if repository exists
    list_repository_response = devops_client.list_repositories(project_id=toolkit_project_id,name=repo_name).data
    repo_state = ""
    if list_repository_response.items:
        for item in list_repository_response.items:
            repo_state = item.lifecycle_state
        if repo_state != "ACTIVE":
            print("Repository exists with name("+repo_name+") but is not in ACTIVE state. Please retry with different customer_name. Exiting...")
            exit(1)
        else:
            toolkit_project_id = item.id
            repo_url = item.ssh_url
            print("Repository exists with name("+repo_name+") and is in ACTIVE state. Reusing same.")

    else:
        # Create Repository
        #print("Creating Repository with name(" + repo_name + ").")
        create_repository_response = devops_client.create_repository(
            create_repository_details=oci.devops.models.CreateRepositoryDetails(
                name=repo_name,
                project_id=toolkit_project_id,
                repository_type="HOSTED",
                description="Created by Automation ToolKit")).data
        repo_url = create_repository_response.ssh_url
        print("Waiting for repository ("+repo_name+") to be in ACTIVE state.")
        while repo_state != "ACTIVE":
            devops_repo = devops_client.get_repository(repository_id=create_repository_response.id).data
            repo_state = devops_repo.lifecycle_state
    return repo_url


def update_devops_config(prefix, repo_ssh_url,dir_values,devops_user,devops_user_key,devops_dir,ct):
    # create git config file
    git_config_file_location = "/cd3user/.ssh"
    git_config_file = git_config_file_location + "/config"
    if not os.path.exists(git_config_file_location):
        os.makedirs(git_config_file_location, 0o777)

    file = open(git_config_file, "w")

    file.write("Host devops.scmservice.*.oci.oraclecloud.com\n "
                "StrictHostKeyChecking no\n "
                "User "+str(devops_user)+"\n "
                "IdentityFile "+str(devops_user_key)+"\n")

    os.chmod(git_config_file, 0o600)
    file.close()

    # create jenkins.properties file
    if not os.path.exists(jenkins_home):
        os.mkdir(jenkins_home)
    jenkins_properties_file_path = jenkins_home+"/jenkins.properties"

    if dir_values:
        dir_structure = "Multiple_Outdir"
    else:
        dir_structure = "Single_Outdir"

    file = open(jenkins_properties_file_path, "w+")
    file.write("git_url= \""+repo_ssh_url+"\"\n"
                "regions="+str(ct.all_regions)+"\n"
                "services="+str(dir_values)+"\n"
                "outdir_structure=[\""+dir_structure+"\"]\n")
    file.close()

    '''
    # create setupoci.py job config file

    setupoci_jenkins_config_file_path = open(os.environ['JENKINS_INSTALL']+"/setUpOCI_config.xml", 'r')
    setupoci_jenkins_config_file_data = ""
    for line in setupoci_jenkins_config_file_path.readlines():
        if line.__contains__("<!-- set customer_prefix -->"):
            setupoci_jenkins_config_file_data = setupoci_jenkins_config_file_data+"<!-- set customer_prefix --><command>customer_prefix=\""+prefix+"\"\n"
        else:
            setupoci_jenkins_config_file_data = setupoci_jenkins_config_file_data+line

    f = open(os.environ['JENKINS_INSTALL']+"/setUpOCI_config.xml", 'w+')
    f.write(setupoci_jenkins_config_file_data)
    f.close()
    '''
    # Update Environment variable for jenkins
    yaml_file_path = os.environ['JENKINS_INSTALL'] + "/jcasc.yaml"
    with open(yaml_file_path) as yaml_file:
        cfg = yaml.load(yaml_file, Loader=yaml.FullLoader)
    cfg["jenkins"]["globalNodeProperties"] = [{'envVars': {'env': [{'key': 'customer_prefix', 'value': prefix}]}}]
    with open(yaml_file_path, "w") as yaml_file:
        cfg = yaml.dump(cfg, stream=yaml_file, default_flow_style=False, sort_keys=False)

    local_repo = git.Repo.init(devops_dir)
    f = open(devops_dir + ".gitignore", "w")
    git_ignore_file_data = ".DS_Store\n*tfstate*\n*terraform*\ntfplan.out\ntfplan.json\n*backup*\ntf_import_commands*"
    f.write(git_ignore_file_data)
    f.close()
    existing_remote = local_repo.git.remote()
    if existing_remote == "origin":
        local_repo.delete_remote("origin")
    origin = local_repo.create_remote("origin", repo_ssh_url)
    assert origin.exists()
    assert origin == local_repo.remotes.origin == local_repo.remotes["origin"]
    origin.fetch()  # assure we actually have data. fetch() returns useful information
    # Setup a local tracking branch of a remote branch
    local_repo.create_head("main", origin.refs.main)  # create local branch "main" from remote "main"
    local_repo.heads.main.set_tracking_branch(origin.refs.main)  # set local "master" to track remote "master
    local_repo.heads.main.checkout()  # checkout local "master" to working tree
    local_repo.config_writer().set_value("user", "name", devops_user).release()
    local_repo.config_writer().set_value("user", "email", devops_user).release()

    for f in glob.glob(os.environ['JENKINS_INSTALL'] + "/*.groovy"):
        shutil.copy2(f, devops_dir + "/")

    #shutil.copy(os.environ['JENKINS_INSTALL'] + "/singleOutput.groovy", devops_dir + "/singleOutput.groovy")
    local_repo.git.add('--all')
    commit_id='None'
    try:
        msg = local_repo.git.commit('-m', 'Initial commit from createTenancyConfig.py')
        commit_id = re.search("\[(.*)\]", msg)
        commit_id = commit_id.group(1).split(" ")[1]
        local_repo.git.push()
        print("Initial Commit to DevOps Repository done with commit id: " + commit_id)
    except git.exc.GitCommandError as e:
        if ("nothing to commit, working directory clean" in str(e)):
            print("Nothing to commit to DevOps Repository.")
    except Exception as e:
        print(e)
        print("Exiting...")
        exit()
    return commit_id
def create_bucket(config, signer):
    bucket_region = config.get('region').strip()
    buckets_client = ObjectStorageClient(config=config, retry_strategy=oci.retry.DEFAULT_RETRY_STRATEGY, signer=signer)
    namespace = buckets_client.get_namespace().data
    try:
        buckets_client.get_bucket(namespace, bucket_name).data
        print("Bucket exists with name(" + bucket_name + ") in " + bucket_region + ". Reusing same.")
    except Exception as e:
        #print("\nCreating bucket " + bucket_name + " under root compartment in " + bucket_region+" for remote state...")
        create_bucket_response = buckets_client.create_bucket(
        namespace_name=namespace,
        create_bucket_details=oci.object_storage.models.CreateBucketDetails(name=bucket_name,compartment_id=compartment_ocid,versioning='Enabled'))
    return bucket_region,bucket_name


# Execution of code begins here
parser = argparse.ArgumentParser(description="Connects the container to tenancy")
parser.add_argument("propsfile", help="Full Path of properties file. eg tenancyconfig.properties")
args = parser.parse_args()
config = configparser.RawConfigParser()
config.read(args.propsfile)

# Initialize Toolkit Variables
user_dir = "/cd3user"
auto_keys_dir = user_dir + "/tenancies/keys"
toolkit_dir = user_dir +"/oci_tools/cd3_automation_toolkit"
modules_dir = toolkit_dir + "/user-scripts/terraform"
variables_example_file = modules_dir + "/variables_example.tf"
setupoci_props_toolkit_file_path = toolkit_dir + "/setUpOCI.properties"
jenkins_dir = os.environ['JENKINS_INSTALL']

global topic_name
global project_name
global repo_name
global commit_id
global bucket_name
global jenkins_home

# Read Config file Variable
prefix = config.get('Default', 'customer_name').strip()
if prefix == "" or prefix == "\n":
    print("Invalid Prefix. Please try again......Exiting !!")
    exit(1)

# Initialize Tenancy Variables
customer_tenancy_dir = user_dir + "/tenancies/" + prefix
terraform_files = customer_tenancy_dir + "/terraform_files/"
config_file_path = customer_tenancy_dir + "/" + prefix + "_config"
setupoci_props_file_path = customer_tenancy_dir + "/" + prefix + "_setUpOCI.properties"

# Read Config file Variables
try:
    tenancy = config.get('Default', 'tenancy_ocid').strip()
    user=''
    _key_path=''
    fingerprint=''

    if tenancy == "" or tenancy == "\n":
        print("Tenancy ID cannot be left empty...Exiting !!")
        exit(1)

    auth_mechanism = config.get('Default', 'auth_mechanism').strip().lower()
    if auth_mechanism == "" or auth_mechanism == "\n" or (auth_mechanism!='api_key' and auth_mechanism!='session_token' and auth_mechanism!='instance_principal'):
        print("Auth Mechanism cannot be left empty...Exiting !!")
        exit(1)

    if auth_mechanism == 'api_key' or auth_mechanism == 'session_token':
        if auth_mechanism == 'api_key':
            print("=================================================================")
            print("NOTE: Make sure the API Public Key is added to the OCI Console!!!")
            print("=================================================================")

        fingerprint = config.get('Default', 'fingerprint').strip()
        if fingerprint == "" or fingerprint == "\n":
            print("Fingerprint cannot be left empty...Exiting !!")
            exit(1)

        user = config.get('Default', 'user_ocid').strip()
        if user == "" or user == "\n":
            print("user_ocid cannot be left empty...Exiting !!")
            exit(1)

        key_path = config.get('Default', 'key_path').strip()
        if key_path == "" or key_path == "\n":
            key_path = auto_keys_dir +"/oci_api_private.pem"
        if not os.path.isfile(key_path):
            print("Invalid PEM Key File at "+key_path+". Please try again......Exiting !!")
            exit(1)

        if auth_mechanism == 'session_token':
            session_token_file = config.get('Default', 'security_token_file').strip()
            if session_token_file == "" or session_token_file == "\n" or not os.path.isfile(session_token_file):
                print("Invalid path for Session Token File...Exiting !!")
                exit(1)

    region = config.get('Default', 'region').strip()
    if (region == ''):
        region = "us-ashburn-1"
    rg=region

    outdir_structure_file = config.get('Default', 'outdir_structure_file').strip()
    ssh_public_key = config.get('Default', 'ssh_public_key').strip()

    ## Advanced parameters ##
    remote_state = config.get('Default', 'use_remote_state').strip().lower()
    remote_state_bucket = config.get('Default', 'remote_state_bucket_name').strip()

    use_devops = config.get('Default', 'use_oci_devops_git').strip().strip().lower()
    devops_user = config.get('Default', 'oci_devops_git_user').strip()
    devops_user_key = config.get('Default', 'oci_devops_git_key').strip()

    if use_devops == 'yes':
        #Use remote state if using devops
        remote_state='yes'

        # OCI DevOps GIT User Details are mandatory while using instance_principal
        if auth_mechanism == 'instance_principal':
            if devops_user == "" or devops_user == "\n" or devops_user_key == "" or devops_user_key == "\n":
                print("OCI DevOps GIT User Details cannot be left empty when using instance_principal...Exiting !!")
                exit(1)

        # Use same user and key as $user_ocid and $key_path for OCI Devops GIT operations
        if devops_user == '' or devops_user=="\n":
            devops_user = user
        if devops_user_key == '' or devops_user_key=="\n":
            devops_user_key = customer_tenancy_dir+"/"+os.path.basename(key_path)


    if remote_state == 'yes':
        # Use same oci_devops_git_user for managing terraform remote state backend
        remote_state_user=devops_user

        # Bucket Name
        if remote_state_bucket == '' or remote_state_bucket == "\n":
            bucket_name = prefix + "-automation-toolkit-bucket"
        else:
            bucket_name = remote_state_bucket.strip()

    compartment_ocid = config.get('Default', 'compartment_ocid').strip()
    if compartment_ocid == '' or compartment_ocid == '\n':
        compartment_ocid = tenancy


except Exception as e:
    print(e)
    print('Check if input properties exist and try again..exiting...')
    exit()


if not os.path.exists(customer_tenancy_dir):
    os.makedirs(customer_tenancy_dir)
dir_values = []

# 1. Move outdir_structure_file
_outdir_structure_file = ''
if (outdir_structure_file != '' and outdir_structure_file != "\n"):
    if not os.path.isfile(outdir_structure_file):
        print("Invalid outdir_structure_file. Please provide correct file path......Exiting !!")
        exit(1)
    else:
        outdir_config = configparser.RawConfigParser()
        outdir_config.read(outdir_structure_file)
        for key, value in outdir_config.items("Default"):
            if value == '':
                print("Out Directory is missing for one or more parameters, for eg. " + key)
                print("Please check " + outdir_structure_file)
                exit(1)
            if value not in dir_values:
                dir_values.append(str(value))

        _outdir_structure_file = customer_tenancy_dir + "/" + prefix + "_outdir_structure_file"
        #if not os.path.exists(_outdir_structure_file):
        shutil.copyfile(outdir_structure_file, _outdir_structure_file)
    print("\nUsing different directories for OCI services as per the input outdir_structure_file..........")
else:
    print("\nUsing single out directory for resources..........")


# 2. Move Private PEM key and Session Token file
_session_token_file=''
_key_path = ''
if auth_mechanism=='api_key' or auth_mechanism=='session_token':
    print("\nMoving Private Key File..........")
    # Move Private PEM Key File
    filename = os.path.basename(key_path)
    shutil.copy(key_path, key_path + "_backup_"+ datetime.datetime.now().strftime("%d-%m-%H%M%S").replace('/', '-'))
    shutil.move(key_path, customer_tenancy_dir + "/" + filename)
    _key_path = customer_tenancy_dir + "/" + filename
    os.chmod(_key_path,0o600)

    # Move Session Token File
    if auth_mechanism == 'session_token':
        print("\nMoving Session Token File..........")
        filename = os.path.basename(session_token_file)
        shutil.copy(session_token_file,session_token_file+"_backup_"+ datetime.datetime.now().strftime("%d-%m-%H%M%S").replace('/', '-'))
        shutil.move(session_token_file, customer_tenancy_dir+"/"+filename)
        _session_token_file = customer_tenancy_dir + "/" + filename

# 3. Create config file
#if not os.path.isfile(config_file_path):
print("\nCreating Tenancy specific config.................")#, terraform provider , variables and properties files.................")
file = open(config_file_path, "w")
if auth_mechanism=='api_key':
    file.write("[DEFAULT]\n"
               "tenancy = "+tenancy+"\n"
                                    "fingerprint = "+fingerprint+"\n"
                                                                 "user = "+user+"\n"
                                                                                "key_file = "+_key_path+"\n"
                                                                                                        "region = "+region+"\n")

elif auth_mechanism=='session_token':
    file.write("[DEFAULT]\n"
               "tenancy = "+tenancy+"\n"
                                    "fingerprint = "+fingerprint+"\n"
                                                                 "security_token_file = "+_session_token_file+"\n"
                                                                                                              "user = "+user+"\n"
                                                                                                                             "key_file = "+_key_path+"\n"
                                                                                                                                                     "region = "+region+"\n")
    # Copy config file at home location also for TF to work with SSO token
    shutil.copy(config_file_path, os.path.expanduser( '~' )+"/.oci")
elif auth_mechanism=='instance_principal':
    file.write("[DEFAULT]\n"
               "tenancy = "+tenancy+"\n"
                                    "region = "+region+"\n")

file.close()
tenancy_id=tenancy

## Authenticate
ct = commonTools()
config, signer = ct.authenticate(auth_mechanism, config_file_path)
ct.get_subscribedregions(config,signer)
home_region = ct.home_region

## Check the remote state requirements
backend_file = open(modules_dir + "/backend.tf", 'r')
backend_file_data = backend_file.readlines()
global_backend_file_data = ""

if remote_state == "yes":
    print("\nCreating Tenancy specific remote tfstate Items - bucket, aws credentials.................")
    s3_credential_file_path = customer_tenancy_dir + "/" + prefix + "_s3_credentials"
    buckets_client = ObjectStorageClient(config=config,
                                         retry_strategy=oci.retry.DEFAULT_RETRY_STRATEGY,
                                         signer=signer)
    namespace = buckets_client.get_namespace().data
    bucket_region,bucket_name=create_bucket(config,signer)
    try:
        # Generate customer_secret_keys for remote state credentials
        new_config = deepcopy(config)
        new_config.__setitem__("region", ct.region_dict[home_region])

        identity_client = oci.identity.IdentityClient(config=new_config, retry_strategy=oci.retry.DEFAULT_RETRY_STRATEGY,signer=signer)
        cred_name = prefix+"-automation-toolkit-csk"

        # Get user ocid for DevOps User Name
        if "ocid1.user.oc1" not in remote_state_user:
            if '@' in remote_state_user:
                remote_state_user = remote_state_user.rsplit("@",1)[0]

            identity_client = oci.identity.IdentityClient(config=new_config,
                                                          retry_strategy=oci.retry.DEFAULT_RETRY_STRATEGY,
                                                          signer=signer)
            user_data = identity_client.list_users(compartment_id=tenancy,name=remote_state_user).data
            remote_state_user = user_data[0].id

        # check if credential exists
        list_customer_secret_key_response = identity_client.list_customer_secret_keys(user_id=remote_state_user).data
        for keys in list_customer_secret_key_response:
            if keys.display_name == cred_name:
                print("Another Customer secret key exists with same name. Deleting existing key and creating new key...")
                customer_secret_key_id = keys.id
                identity_client.delete_customer_secret_key(user_id=remote_state_user,customer_secret_key_id=customer_secret_key_id)
        create_customer_secret_key_response = identity_client.create_customer_secret_key(
            create_customer_secret_key_details=oci.identity.models.CreateCustomerSecretKeyDetails(
                display_name=cred_name),
            user_id=remote_state_user).data
        credential_file_data="[default]\naws_access_key_id="+str(create_customer_secret_key_response.id)+"\naws_secret_access_key="+create_customer_secret_key_response.key+"\n"
    except Exception as e:
        print(e)
        # Add code to ask domain name/url and generate creds

    f = open(f"{s3_credential_file_path}", "w+")
    f.write(credential_file_data)
    f.close()

    for line in backend_file_data:
        if line.__contains__("This line will be removed when using remote state"):
            continue
        elif line.__contains__("key      = "):
            global_backend_file_data += "    key      = \"" +  "global/terraform.tfstate\"\n"
        elif line.__contains__("bucket   = "):
            global_backend_file_data += "    bucket   = \"" + bucket_name + "\"\n"
        elif line.__contains__("region   = "):
            global_backend_file_data += "    region   = \"" + bucket_region + "\"\n"
        elif line.__contains__("endpoint = "):
            global_backend_file_data += "    endpoint = \"https://" + namespace + ".compat.objectstorage." + bucket_region + ".oraclecloud.com\"\n"
        elif line.__contains__("shared_credentials_file     = "):
            global_backend_file_data += "    shared_credentials_file     = \"" + s3_credential_file_path + "\"\n"
        else:
            global_backend_file_data += line
else:
    for line in backend_file_data:
        global_backend_file_data += line


## Fetch OCI_regions
cd3service = cd3Services()
print("")
cd3service.fetch_regions(config, signer)

'''
# 3. Fetch AD Names and write to config file
print('Fetching AD names from tenancy and writing to config file if it does not exist.............')
identity_client = oci.identity.IdentityClient(config=config,signer=signer)
conf_file = open(config_file_path, "a")
tenancy_id = tenancy
i = 1
for ad in paginate(identity_client.list_availability_domains, compartment_id=tenancy_id):
    ad_name = "ad_" + str(i)
    if not ad_name in config:
        conf_file.write("ad_" + str(i) + "=" + ad.name + "\n")
    i = i + 1
conf_file.close()
'''

# 4. Generate setUpOCI.properties file
#if not os.path.isfile(setupoci_props_file_path):
print("Creating Tenancy specific setUpOCI.properties.................")
with open(setupoci_props_toolkit_file_path, 'r+') as setUpOci_file:
    setupoci_props_toolkit_file_data = setUpOci_file.read().rstrip()

setupoci_props_toolkit_file_data = setupoci_props_toolkit_file_data.replace("outdir=", "outdir="+terraform_files)
setupoci_props_toolkit_file_data = setupoci_props_toolkit_file_data.replace("prefix=", "prefix="+prefix)
setupoci_props_toolkit_file_data = setupoci_props_toolkit_file_data.replace("auth_mechanism=", "auth_mechanism=" + auth_mechanism)
setupoci_props_toolkit_file_data = setupoci_props_toolkit_file_data.replace("config_file=", "config_file="+config_file_path)
setupoci_props_toolkit_file_data = setupoci_props_toolkit_file_data.replace("outdir_structure_file=", "outdir_structure_file="+_outdir_structure_file)

f = open(setupoci_props_file_path, "w+")
f.write(setupoci_props_toolkit_file_data)
f.close()

# 5. Fetch Subscribed regions and create the TF related files for each region
if not os.path.exists(terraform_files):
    os.makedirs(terraform_files)


print("Creating Tenancy specific region directories, terraform provider , variables files.................")

for region in ct.all_regions:
    # Rerunning createTenancy for any new region subscription. Process only new region directories else continue
    if os.path.exists(terraform_files+region):
        continue

    os.mkdir(terraform_files+region)

    linux_image_id = ''
    windows_image_id = ''


    new_config = deepcopy(config)
    new_config.__setitem__("region", ct.region_dict[region])
    cc = oci.core.ComputeClient(config=new_config,signer=signer)

    # fetch latest image ocids
    try:
        for image in paginate(cc.list_images, compartment_id=tenancy_id, operating_system='Oracle Linux',
                              sort_by='TIMECREATED'):
            if ("Gen2-GPU" not in image.display_name):
                linux_image_id = image.id
                break
        for image in paginate(cc.list_images, compartment_id=tenancy_id, operating_system='Windows',
                              sort_by='TIMECREATED'):
            if ("Gen2-GPU" not in image.display_name):
                windows_image_id= image.id
                break
    except Exception as e:
        print(e)
        print("!!! Could not fetch the list of images for Windows and Oracle Linux to write to variables_"+region+".tf file!!!\n"
                                                                                                                  "Please make sure to have Read Access to the Tenancy at the minimum !!!")
        print("\nContinuing without fetching Image OCIDs........!!!")

    # 6. Read variables.tf from examples folder and copy the variables as string
    with open(variables_example_file, 'r+') as var_eg_file:
        variables_example_file_data = var_eg_file.read().rstrip()

    variables_example_file_data = variables_example_file_data.replace("<TENANCY OCID HERE>", tenancy)
    variables_example_file_data = variables_example_file_data.replace("<USER OCID HERE>", user)
    variables_example_file_data = variables_example_file_data.replace("<SSH KEY FINGERPRINT HERE>", fingerprint)
    variables_example_file_data = variables_example_file_data.replace("<SSH PRIVATE KEY FULL PATH HERE>", _key_path)
    variables_example_file_data = variables_example_file_data.replace("<OCI TENANCY REGION HERE eg: us-phoenix-1 or us-ashburn-1>", ct.region_dict[region])
    variables_example_file_data = variables_example_file_data.replace("<SSH PUB KEY STRING HERE>", ssh_public_key)
    if (windows_image_id != ''):
        variables_example_file_data = variables_example_file_data.replace("<LATEST WINDOWS OCID HERE>", windows_image_id)

    if (linux_image_id != ''):
        variables_example_file_data = variables_example_file_data.replace("<LATEST LINUX OCID HERE>", linux_image_id)

    f = open(terraform_files+"/"+region+"/variables_" + region + ".tf", "w+")
    f.write(variables_example_file_data)
    f.close()


    # Global dir for RPC related
    if region == ct.home_region:
        if not os.path.exists(f"{terraform_files}/global/rpc"):
            os.makedirs(f"{terraform_files}/global/rpc")
        shutil.copyfile(modules_dir + "/provider.tf", f"{terraform_files}/global/rpc/provider.tf")

        with open(f"{terraform_files}/global/rpc/provider.tf", 'r+') as provider_file:
            provider_file_data = provider_file.read().rstrip()
        if auth_mechanism == 'instance_principal':
            provider_file_data = provider_file_data.replace("provider \"oci\" {", "provider \"oci\" {\nauth = \"InstancePrincipal\"")
        if auth_mechanism == 'session_token':
            provider_file_data = provider_file_data.replace("provider \"oci\" {", "provider \"oci\" {\nauth = \"SecurityToken\"\nconfig_file_profile = \"DEFAULT\"")

        f = open(f"{terraform_files}/global/rpc/provider.tf", "w+")
        f.write(provider_file_data)
        f.close()

        f = open(f"{terraform_files}/global/rpc/variables_global.tf", "w+")
        f.write(variables_example_file_data)
        f.close()

        f = open(f"{terraform_files}/global/rpc/backend.tf", "w+")
        f.write(global_backend_file_data)
        f.close()

    # 7. Copy terraform modules and variables file to outdir
    distutils.dir_util.copy_tree(modules_dir, terraform_files +"/" + region)
    with open(terraform_files +"/" + region + "/provider.tf", 'r+') as provider_file:
        provider_file_data = provider_file.read().rstrip()
    if auth_mechanism == 'instance_principal':
        provider_file_data = provider_file_data.replace("provider \"oci\" {",
                                                        "provider \"oci\" {\nauth = \"InstancePrincipal\"")
    if auth_mechanism == 'session_token':
        provider_file_data = provider_file_data.replace("provider \"oci\" {",
                                                        "provider \"oci\" {\nauth = \"SecurityToken\"\nconfig_file_profile = \"DEFAULT\"")
    f = open(terraform_files +"/" + region + "/provider.tf", "w+")
    f.write(provider_file_data)
    f.close()

    reg_backend = open(terraform_files +"/" + region + "/backend.tf",'w+')
    reg_backend.write(global_backend_file_data)
    reg_backend.close()
    reg_backend = open(terraform_files + "/" + region + "/backend.tf", 'r+')
    new_backend_data = ""

    for line in reg_backend.readlines():
        if line.__contains__("key      = "):
            new_backend_data += "    key      = \"" + region + "/terraform.tfstate\"\n"
        else:
            new_backend_data += line
    reg_backend.close()
    rewrite_backend = open(terraform_files + "/" + region + "/backend.tf", 'w')
    rewrite_backend.write(new_backend_data)
    rewrite_backend.close()

    # Manage multiple outdir
    if (outdir_structure_file == '' or outdir_structure_file == "\n"):
        pass
    else:
        region_dir = terraform_files + "/" + region + "/"
        for service, service_dir in outdir_config.items("Default"):
            service = service.strip().lower()
            service_dir = service_dir.strip()

            # Keep the .tf file in default region directory if directory name is empty
            if service_dir=="" or service_dir == "\n":
                continue
            #if (service != 'identity' and service != 'tagging') or ((service == 'identity' or service == 'tagging') and region == home_region):
            home_region_services = ['identity', 'tagging', 'budget']
            if (region != home_region) and (service in home_region_services):
                os.remove(region_dir + service + ".tf")

            if (service not in home_region_services) or ((service in home_region_services) and region == home_region):
                region_service_dir = region_dir + service_dir
                if not os.path.exists(region_service_dir):
                    os.mkdir(region_service_dir)
                if (service == 'instance'):
                    if(os.path.isdir(region_service_dir+'/scripts')):
                        shutil.rmtree(region_service_dir+'/scripts')
                    shutil.move(region_dir + 'scripts',region_service_dir+'/')
                with open(region_dir + service + ".tf", 'r+') as tf_file:
                    module_data = tf_file.read().rstrip()
                    module_data = module_data.replace("\"./modules", "\"../modules")

                f = open(region_service_dir + "/" + service + ".tf", "w+")
                f.write(module_data)
                f.close()
                os.remove(region_dir + service + ".tf")

                shutil.copyfile(region_dir + "variables_" + region + ".tf", region_service_dir + "/" + "variables_" + region + ".tf")
                shutil.copyfile(region_dir + "provider.tf", region_service_dir + "/" + "provider.tf")
                shutil.copyfile(region_dir + "oci-data.tf", region_service_dir + "/" + "oci-data.tf")

                # write backend.tf to respective directories
                reg_service_backend = open(region_service_dir + "/backend.tf", 'w+')
                reg_service_backend.write(global_backend_file_data)
                reg_service_backend.close()
                reg_service_backend = open(region_service_dir + "/backend.tf", 'r+')
                new_backend_data = ""

                for line in reg_service_backend.readlines():
                    if line.__contains__("key      = "):
                        new_backend_data += "    key      = \"" + region+"/"+service_dir + "/terraform.tfstate\"\n"
                    else:
                        new_backend_data += line
                reg_service_backend.close()
                rewrite_backend = open(terraform_files + "/" + region+"/"+service_dir + "/backend.tf", 'w')
                rewrite_backend.write(new_backend_data)
                rewrite_backend.close()


        os.remove(terraform_files + "/" + region + "/" + "variables_" + region + ".tf")
        os.remove(terraform_files + "/" + region + "/" + "provider.tf")
        os.remove(terraform_files + "/" + region + "/" + "oci-data.tf")
        os.remove(terraform_files + "/" + region + "/" + "backend.tf")

    # 8. Remove terraform example variable file from outdir
    os.remove(terraform_files + "/" + region + "/variables_example.tf")

# 9. Update DevOps files and configurations
if use_devops == 'yes':
    print("\nCreating Tenancy specific DevOps Items - Topic, Project and Repository.................")
    topic_name = prefix + "-automation-toolkit-topic"
    project_name = prefix + "-automation-toolkit-project"
    repo_name = prefix + "-automation-toolkit-repo"

    repo_ssh_url = create_devops_resources(config, signer)
    devops_dir = terraform_files
    jenkins_home = os.environ['JENKINS_HOME']

    #Get Username from $user_ocid if $oci_devops_git_user is left empty
    if "ocid1.user.oc1" in devops_user:
        identity_client = oci.identity.IdentityClient(config=new_config,
                                                      retry_strategy=oci.retry.DEFAULT_RETRY_STRATEGY,
                                                      signer=signer)
        user_data=identity_client.get_user(user_id=user).data
        tenancy_data=identity_client.get_tenancy(tenancy_id=tenancy).data
        devops_user=user_data.name+"@"+tenancy_data.name

    commit_id = update_devops_config(prefix, repo_ssh_url, dir_values, devops_user, devops_user_key, devops_dir, ct)

del ct, config, signer
# Logging information
logging.basicConfig(filename=customer_tenancy_dir+'/cmds.log', format='%(message)s', filemode='w', level=logging.INFO)

print("==================================================================================================================================")
print("\nThe toolkit has been setup to execute API's successfully. !!!\n")
#print("Customer Specific Working Directory Path: "+customer_tenancy_dir)
#print("Config File Path: "+ config_file_path )
#print("Path to region based directories, terraform provider and the variables files: " + terraform_files)
#print("\nPlease use "+prefix+"_setUpOCI.properties file at "+customer_tenancy_dir +" to proceed with the execution of the SetUpOCI script !!!!")
#print("Update the path of CD3 Excel input file in "+customer_tenancy_dir + "/" +prefix+"_setUpOCI.properties before executing the next command......")
#print("\nCommands to execute: (Alternately, you may also check the cmds.log in outdir for the same information)")
logging.info("##############################")
logging.info("Output Information")
logging.info("##############################")
logging.info("Customer Specific Working Directory Path: "+customer_tenancy_dir)
if use_devops == "yes":
    logging.info("Common Jenkins Home: " +jenkins_home)
    logging.info("DevOps Project Name and Repo Name: "+project_name+ ", "+repo_name+ " in "+rg+".")
    logging.info("Folder configured for OCI DevOps GIT: "+terraform_files+" Initial Commit ID from createTenancyConfig.py: "+commit_id)
if remote_state == 'yes':
    logging.info("Remote State Bucket Name: "+ bucket_name+ " in "+rg+".")

logging.info("\n##############################")
logging.info("Commands to Execute")
logging.info("##############################")
if use_devops=='yes':
    logging.info("/usr/share/jenkins/jenkins.sh &")

logging.info("Commands via CLI - ")
logging.info("cd "+user_dir+"/oci_tools/cd3_automation_toolkit/")
#print("python setUpOCI.py "+customer_tenancy_dir + "/" +prefix+"_setUpOCI.properties")
logging.info("python setUpOCI.py "+customer_tenancy_dir + "/" +prefix+"_setUpOCI.properties")

with open(customer_tenancy_dir + '/cmds.log', 'r') as log_file:
    data = log_file.read().rstrip()
print(data)

print("==================================================================================================================================")

