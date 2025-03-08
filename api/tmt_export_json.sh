#!/bin/bash

# Clone a git repository and export tmt test to a json file
# Expect 3 arguments
# 1: Url of the git test repository
# 2: Branch of the git test repository
# 3: Destination path where the exported json should be saved

repository=$1
repository_branch=$2
dest_path=$3

current_datetime=$(date +"%Y%m%d%H%M%S")
tmp_dir=$(mktemp -d)
pushd $tmp_dir

git clone --branch ${repository_branch} --depth 1 ${repository} repo 2> /dev/null
cd repo
repo_name=$(basename ${repository}) 
dest_filename=${repo_name}_${current_datetime}.json
dest_filepath=${dest_path}/${dest_filename}
log_filename=${repo_name}_${current_datetime}.log
log_filepath=${dest_path}/${log_filename}

echo ${log_file}

echo "-----------" >> ${log_filepath}
echo "Repo: ${repository}" >> ${log_filepath}
echo "Branch: ${repository_branch}" >> ${log_filepath}
echo "Timestamp: ${current_datetime}" >> ${log_filepath}
echo "Tmp dir: ${tmp_dir}" >> ${log_filepath}
echo "-----------" >> ${log_filepath}
ls -la >> ${log_filepath}
echo "-----------" >> ${log_filepath}
tmt test ls >> ${log_filepath}
echo "-----------" >> ${log_filepath}

tmt test export --how json > tmt_export.json
jq --arg url "${repository}" \
   --arg ref "${repository_branch}" \
   --arg datetime "${current_datetime}" \
   --arg repo_commit "$(git rev-parse HEAD)" \
   '{repository: $url, branch: $ref, datetime: $datetime, repo_commit: $repo_commit, test_cases: .}' tmt_export.json > ${dest_filepath}

echo $? >> ${log_filepath}
echo "-----------" >> ${log_filepath}

popd
rm -fr $tmp_dir
