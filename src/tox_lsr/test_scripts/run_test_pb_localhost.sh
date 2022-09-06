#!/bin/bash

set -euo pipefail

if [ -n "${LSR_DEBUG:-}" ]; then
    set -x
fi

#EXCLUDETAGS_CORE="${EXCLUDETAGS:-tests::expfail,tests::slow,tests::reboot,tests::multihost_localhost,tests::avc,tests::nvme,tests::scsi,tests::lvm,tests::no_serialization,tests::infiniband}"
SKIP_TAGS="${SKIP_TAGS:-tests::reboot,tests::multihost_localhost,tests::nvme,tests::scsi,tests::infiniband}"
WORK_DIR="${WORK_DIR:-$(mktemp -d lsr_XXXXXXXXXX_work)}"
COLLECTION_BASE_PATH="${COLLECTION_BASE_PATH:-$WORK_DIR}"
PLUGIN_DIR="${PLUGIN_DIR:-$WORK_DIR/plugins}"
PLUGIN_TMP_DIR="${PLUGIN_TMP_DIR:-$WORK_DIR/plugins_tmp}"
REPO_PATH="${REPO_PATH:-$(pwd)}"
LSR_TEST_DIR="${LSR_TEST_DIR:-$REPO_PATH/tests}"
REPO_NAME="${REPO_NAME:-$PACKIT_FULL_REPO_NAME}"
COLLECTION_NAMESPACE="${COLLECTION_NAMESPACE:-fedora}"
COLLECTION_NAME="${COLLECTION_NAME:-linux_system_roles}"
export ANSIBLE_COLLECTIONS_PATHS="${ANSIBLE_COLLECTIONS_PATHS:-$COLLECTION_BASE_PATH}"

if [ -z "${LSR_TEST_PB:-}" ] && [ -n "${1:-}" ]; then
    LSR_TEST_PB="$1"
fi

install_collection_requirements() {
    if [ -f "$REPO_PATH/meta/collection-requirements.yml" ]; then
        ansible-galaxy collection install -U -p "$COLLECTION_BASE_PATH" -vv -r "$REPO_PATH/meta/collection-requirements.yml"
    fi
}

setup_plugins() {
    if [ "${LSR_CONTAINER_PRETTY:-true}" = true ] || [ "${LSR_CONTAINER_PROFILE:-true}" = true ]; then
        local callback_plugin_dir
        callback_plugin_dir="$PLUGIN_DIR"
        if [ ! -d "$callback_plugin_dir" ]; then
            mkdir -p "$callback_plugin_dir"
        fi
        local debug_py
        local profile_py
        debug_py="$callback_plugin_dir/debug.py"
        profile_py="$callback_plugin_dir/profile_tasks.py"
        local need_debug_py
        local need_profile_py
        if [ "${LSR_CONTAINER_PRETTY:-true}" = true ] && [ ! -f "$debug_py" ]; then
            need_debug_py=1
        fi
        if [ "${LSR_CONTAINER_PROFILE:-true}" = true ] && [ ! -f "$profile_py" ]; then
            need_profile_py=1
        fi
        if [ -n "${need_debug_py:-}" ] || [ -n "${need_profile_py:-}" ]; then
            ansible-galaxy collection install -U -p "$PLUGIN_TMP_DIR" -vv ansible.posix
            tmp_debug_py="$PLUGIN_TMP_DIR/ansible_collections/ansible/posix/plugins/callback/debug.py"
            tmp_profile_py="$PLUGIN_TMP_DIR/ansible_collections/ansible/posix/plugins/callback/profile_tasks.py"
            if [ -n "${need_debug_py:-}" ]; then
                mv "$tmp_debug_py" "$debug_py"
            fi
            if [ -n "${need_profile_py:-}" ]; then
                mv "$tmp_profile_py" "$profile_py"
            fi
            rm -rf "$PLUGIN_TMP_DIR/ansible_collections"
        fi
        if [ "${LSR_CONTAINER_PRETTY:-true}" = true ]; then
            export ANSIBLE_STDOUT_CALLBACK=debug
        fi
        if [ "${LSR_CONTAINER_PROFILE:-true}" = true ]; then
            if ansible-config list | grep -q 'name: ANSIBLE_CALLBACKS_ENABLED$'; then
                export ANSIBLE_CALLBACKS_ENABLED=profile_tasks
            else
                export ANSIBLE_CALLBACK_WHITELIST=profile_tasks
            fi
        fi
        export ANSIBLE_CALLBACK_PLUGINS="$callback_plugin_dir"
    else
        unset ANSIBLE_CALLBACK_PLUGINS
        unset ANSIBLE_CALLBACKS_ENABLED
        unset ANSIBLE_CALLBACK_WHITELIST
        unset ANSIBLE_STDOUT_CALLBACK
    fi
}

prepare_control_node() {
    # pre-setup
    # setup repos
    # install control node packages
    # other control node config
    # post-setup
    install_collection_requirements
    setup_plugins
}

prepare_managed_node() {
    # pre-setup
    # setup repos
    # install control node packages
    # other control node config
    # post-setup
    # disk_provisioner for storage role
    echo TODO
}

convert_to_collection() {
    local base_url lsr_role2coll_path lsr_runtime_path role_dest test_dest test_basename
    base_url=https://raw.githubusercontent.com/linux-system-roles/auto-maintenance/master
    lsr_role2coll_path="$WORK_DIR/lsr_role2collection.py"
    lsr_runtime_path="$WORK_DIR/runtime.yml"
    curl -s -o "$lsr_role2coll_path" "$base_url/lsr_role2collection.py"
    curl -s -o "$lsr_runtime_path" "$base_url/lsr_role2collection/runtime.yml"
    role_dest="$COLLECTION_BASE_PATH/ansible_collections/$COLLECTION_NAMESPACE/$COLLECTION_NAME/roles/$REPO_NAME"
    test_dest="$COLLECTION_BASE_PATH/ansible_collections/$COLLECTION_NAMESPACE/$COLLECTION_NAME/tests/$REPO_NAME"
    rm -rf "$role_dest" "$test_dest"
    python3 "$lsr_role2coll_path" --src-owner linux-system-roles --role "$REPO_NAME" \
        --src-path "$REPO_PATH" --dest-path "$COLLECTION_BASE_PATH" \
        --namespace "$COLLECTION_NAMESPACE" --collection "$COLLECTION_NAME" \
        --subrole-prefix "private_${REPO_NAME}_subrole_" \
        --meta-runtime "$lsr_runtime_path"
    # move the tests to the tests tmp dir
    LSR_TEST_DIR="$WORK_DIR/tests"
    mv "$test_dest" "$LSR_TEST_DIR"
    # change the test pb name
    test_basename="$(basename $LSR_TEST_PB)"
    LSR_TEST_PB="$LSR_TEST_DIR/$test_basename"
}

setup_vault() {
    local test_basename no_vault_vars vault_pwd_file vault_vars_file
    vault_pwd_file="$LSR_TEST_DIR/vault_pwd"
    vault_vars_file="$LSR_TEST_DIR/vars/vault-variables.yml"
    no_vault_vars="$LSR_TEST_DIR/no-vault-variables.txt"
    if [ -f "$vault_pwd_file" ] && [ -f "$vault_vars_file" ]; then
        export ANSIBLE_VAULT_PASSWORD_FILE="$vault_pwd_file"
        vault_args="--extra-vars=@$vault_vars_file"
        test_basename="$(basename "$LSR_TEST_PB")"
        if [ -f "$no_vault_vars" ] && grep -q "^${test_basename}$" "$no_vault_vars"; then
            unset ANSIBLE_VAULT_PASSWORD_FILE
            vault_args=""
        fi
    else
        unset ANSIBLE_VAULT_PASSWORD_FILE
        vault_args=""
    fi
}

run_ansible_playbooks() {
    setup_vault
    cd "$LSR_TEST_DIR"
    ansible-playbook -vv --skip-tags="$SKIP_TAGS" "$vault_args" \
        -e ansible_playbook_filepath="$(type -p ansible-playbook)" \
        -c local -i localhost, "$LSR_TEST_PB"
}

prepare_control_node

prepare_managed_node

if [ "${USE_COLLECTION:-false}" = true ]; then
    convert_to_collection
fi

run_ansible_playbooks
