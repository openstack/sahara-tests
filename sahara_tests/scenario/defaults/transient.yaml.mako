<%page args="is_proxy_gateway='true', use_auto_security_group='true', ci_flavor_id='m1.small', availability_zone='nova', volumes_availability_zone='nova'"/>

clusters:
  - plugin_name: vanilla
    plugin_version: 2.7.1
    image: ${vanilla_271_image}
    node_group_templates:
      - name: worker
        flavor: ${ci_flavor_id}
        node_processes:
          - datanode
          - nodemanager
        volumes_per_node: 2
        volumes_size: 2
        availability_zone: ${availability_zone}
        volumes_availability_zone: ${volumes_availability_zone}
        auto_security_group: ${use_auto_security_group}
        node_configs:
          &ng_configs
          MapReduce:
            yarn.app.mapreduce.am.resource.mb: 256
            yarn.app.mapreduce.am.command-opts: -Xmx256m
          YARN:
            yarn.scheduler.minimum-allocation-mb: 256
            yarn.scheduler.maximum-allocation-mb: 1024
            yarn.nodemanager.vmem-check-enabled: false
      - name: master
        flavor: ${ci_flavor_id}
        node_processes:
          - oozie
          - historyserver
          - resourcemanager
          - namenode
        auto_security_group: ${use_auto_security_group}
        is_proxy_gateway: ${is_proxy_gateway}
    cluster_template:
      name: transient
      node_group_templates:
        master: 1
        worker: 3
      cluster_configs:
        HDFS:
          dfs.replication: 1
        MapReduce:
          mapreduce.tasktracker.map.tasks.maximum: 16
          mapreduce.tasktracker.reduce.tasks.maximum: 16
        YARN:
          yarn.resourcemanager.scheduler.class: org.apache.hadoop.yarn.server.resourcemanager.scheduler.fair.FairScheduler
    cluster:
      name: ${cluster_name}
      is_transient: true
    scenario:
      - run_jobs
      - transient
    edp_jobs_flow: pig_job

