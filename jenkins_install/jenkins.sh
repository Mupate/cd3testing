#! /bin/bash -e

: "${REF:="/usr/share/jenkins/x``"}"

# Check if JENKINS_HOME exists
if [ ! -d "$JENKINS_HOME" ]; then
    # If it doesn't exist, create it
    mkdir -p "$JENKINS_HOME"
    echo "Directory created: $JENKINS_HOME"
fi
cp ${JENKINS_INSTALL}/jcasc.yaml "$JENKINS_HOME/"

if [ ! -d "$JENKINS_HOME/jobs/setUpOCI" ]; then
  mkdir -p "$JENKINS_HOME/jobs/setUpOCI"
fi
cp ${JENKINS_INSTALL}/setUpOCI_config.xml "$JENKINS_HOME/jobs/setUpOCI/config.xml"
cp -r ${JENKINS_INSTALL}/scriptler $JENKINS_HOME

touch "${COPY_REFERENCE_FILE_LOG}" || { echo "Can not write to ${COPY_REFERENCE_FILE_LOG}. Wrong volume permissions?"; exit 1; }
echo "--- Copying files at $(date)" >> "$COPY_REFERENCE_FILE_LOG"
find "${REF}" \( -type f -o -type l \) -exec bash -c '. ${JENKINS_INSTALL}/jenkins-support; for arg; do copy_reference_file "$arg"; done' _ {} +


# if `docker run` first argument start with `--` the user is passing jenkins launcher arguments
if [[ $# -lt 1 ]] || [[ "$1" == "--"* ]]; then

  # read JAVA_OPTS and JENKINS_OPTS into arrays to avoid need for eval (and associated vulnerabilities)
  java_opts_array=()
  while IFS= read -r -d '' item; do
    java_opts_array+=( "$item" )
  done < <([[ $JAVA_OPTS ]] && xargs printf '%s\0' <<<"$JAVA_OPTS")

  readonly agent_port_property='jenkins.model.Jenkins.slaveAgentPort'
  if [ -n "${JENKINS_SLAVE_AGENT_PORT:-}" ] && [[ "${JAVA_OPTS:-}" != *"${agent_port_property}"* ]]; then
    java_opts_array+=( "-D${agent_port_property}=${JENKINS_SLAVE_AGENT_PORT}" )
  fi

  if [[ "$DEBUG" ]] ; then
    java_opts_array+=( \
      '-Xdebug' \
      '-Xrunjdwp:server=y,transport=dt_socket,address=5005,suspend=y' \
    )
  fi

  jenkins_opts_array=( )
  while IFS= read -r -d '' item; do
    jenkins_opts_array+=( "$item" )
  done < <([[ $JENKINS_OPTS ]] && xargs printf '%s\0' <<<"$JENKINS_OPTS")

  exec java -Duser.home="$JENKINS_HOME" "${java_opts_array[@]}" -jar ${JENKINS_INSTALL}/jenkins.war "${jenkins_opts_array[@]}" "$@"
fi

# As argument is not jenkins, assume user want to run his own process, for example a `bash` shell to explore this image
exec "$@"
