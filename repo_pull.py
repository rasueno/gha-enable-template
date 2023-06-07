import os
import csv
import git
import shutil
import argparse
from git import Repo

parser = argparse.ArgumentParser(
                    prog = '<---Deleted proprietary info---> GHA repo script',
                    description = 'This script updates the ----files, workflows, and CODEOWNERS files for the specified repo(s), based on the provided template')

parser.add_argument('-r', '--repo', help="Run for a single repo only. This pulls info from the repos.csv file. THIS IGNORES THE ACTIVE FLAG.")
args = vars(parser.parse_args())
repo_flag = False
repo_arg = ""

if (args["repo"]):
    print(f'Running script only for {args["repo"]}')
    repo_flag = True
    repo_arg = args["repo"]


def replace_mustached_tag(string, tag, replacement):
    str = string.replace( '{{' + tag + '}}', replacement) 
    return str     

def replace_mustached_tag_in_file(file, tag, replacement):
    string = ""
    with open(file, "r") as afile:
        string = afile.read()

    str = string.replace( '{{' + tag + '}}', replacement) 
    
    with open(file, "w") as wfile:
        wfile.writelines(str)
        wfile.close()

def copy_and_overwrite(from_path, to_path):
    if os.path.exists(to_path):
        shutil.rmtree(to_path)
    shutil.copytree(from_path, to_path)

if not os.path.exists('./repos'):
    os.makedirs('./repos')


# This function pulls another repo into the ./repos folder you need to setup a secret to work (this was thested under GHE)
def pull_repo(repo_name):
    repo = ""
    if not os.path.exists("./repos/" + repo_name):
        print(f'Pulling...')
        repo = Repo.clone_from("https://" + os.environ["RAFFY_GITHUB_TOKEN"] + "@github.company.com/organization/" + repo_name, "./repos/" + repo_name)
    else:
        print(f'{repo_name} already exists.')
        repo  = Repo(os.path.join("./repos/" + repo_name))
    
    return repo

def switch_branch(repo):
    branches = repo.remotes.origin.refs
    new_head = None

    if("devops_gha_update" in branches):
        new_head = repo.git.checkout("devops_gha_update")
    else:
        new_head = repo.create_head("devops_gha_update")  
        repo.head.set_reference(new_head)

def repo_update_CODEOWNERS_file(repo_name, repo, type):
    print ("Validating CODEOWNERS...")
    if not os.path.exists('./repos/' + repo_name + '/.github'):
        os.makedirs('./repos/' + repo_name + '/.github')

    CODEOWNERS_file_path = "./repos/" + repo_name + "/.github/CODEOWNERS"
    
    CODEOWNERS_content = ""

    if type == "maven":
        CODEOWNERS_content = [
            "/.github/       @comapny/group-admin\n"
        ]
    else:
        CODEOWNERS_content = [
            "/.github/       @comapny/group-admin\n",
            "/helmcharts/    @comapny/group-admin\n"
            "Dockerfile      @comapny/group-admin\n",
            "Jenkinsfile     @comapny/group-admin" 
        ]

    with  open(CODEOWNERS_file_path,'w+') as CODEOWNERS_file:
        CODEOWNERS_file.writelines(CODEOWNERS_content)
        CODEOWNERS_file.close()

    repo.index.add([".github/CODEOWNERS"])

def copy_workflow_files(repo, row):
    print("Copying workflows...")
    if row[2] == "function":
        pass
    elif row[2] == "artifact":
        pass
    elif row[2] == "maven":
        copy_and_overwrite('templates/workflows-mvn', f'./repos/{row[1]}/.github/workflows')

        replace_mustached_tag_in_file('repos/' + row[1] + '/.github/workflows/oneclick-cicd-nonprod.yml', "JAVA_VERSION", row[6])

        repo.index.add([
                f'.github/workflows/oneclick-cicd-nonprod.yml'
            ])
    elif row[2] == "admin":
        copy_and_overwrite('templates/workflows-admin', f'./repos/{row[1]}/.github/workflows')

        repo.index.add([
                f'.github/workflows/update-workflow-all.yml',
                f'.github/workflows/update-workflow.yml'
            ])
    else:
        pass

def update_actionfiles(repo, row):
    pass  # Information was removed as this was proprietary

def gha_update_files(repo, row):
    copy_workflow_files(repo, row)
    # update_actionfiles(repo, row)  # Information was removed as this was proprietary

def commit_changes(repo):
    print("Pushing changes to devops_gha_update branch...")
    repo.index.commit("Updated GHA files.")
    repo.git.push("origin", "devops_gha_update")

def run_process(row):
    print("Processing repo: " + row[1])
    repo = pull_repo(row[1])
    switch_branch(repo)
    repo_update_CODEOWNERS_file(row[1], repo, row[2])
    gha_update_files(repo, row)
    commit_changes(repo)

with open('repos_test.csv') as csvfile:
    csvreader = csv.reader(csvfile, delimiter=',')
    for row in csvreader:
        if(row[1] == "GITHUB_REPO_NAME1"):
            continue
        else:
            if not repo_flag:
                if(row[7] == "on"):
                    run_process(row)
                else:
                    continue

            else:
                if(row[1] == repo_arg):
                    run_process(row)
                else:
                    continue
            
