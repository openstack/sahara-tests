# Copyright (c) 2014 Mirantis Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from testtools import testcase as tc

from tempest.lib import decorators
from tempest.lib.common.utils import data_utils

from sahara_tempest_plugin.tests.api import base as dp_base


class ClusterTemplateTest(dp_base.BaseDataProcessingTest):
    # NOTE: Links to the API documentation: https://docs.openstack.org/
    # api-ref/data-processing/v1.1/#cluster-templates
    # https://docs.openstack.org/api-ref/data-processing/v2/#cluster-templates

    @classmethod
    def skip_checks(cls):
        super(ClusterTemplateTest, cls).skip_checks()
        if cls.default_plugin is None:
            raise cls.skipException("No Sahara plugins configured")

    @classmethod
    def resource_setup(cls):
        super(ClusterTemplateTest, cls).resource_setup()

        # pre-define a node group templates
        node_group_template_w = cls.get_node_group_template('worker1')
        if node_group_template_w is None:
            raise dp_base.InvalidSaharaTestConfiguration(
                message="No known Sahara plugin was found")

        node_group_template_w['name'] = data_utils.rand_name(
            'sahara-ng-template')

        # hack the arguments: keep the compatibility with the signature
        # of self.create_node_group_template
        if 'plugin_version' in node_group_template_w:
            plugin_version_value = node_group_template_w['plugin_version']
            del node_group_template_w['plugin_version']
            node_group_template_w['hadoop_version'] = plugin_version_value

        resp_body = cls.create_node_group_template(**node_group_template_w)
        node_group_template_id = resp_body['id']
        configured_node_group_templates = {'worker1': node_group_template_id}

        cls.full_cluster_template = cls.get_cluster_template(
            configured_node_group_templates)

        # create cls.cluster_template variable to use for comparison to cluster
        # template response body. The 'node_groups' field in the response body
        # has some extra info that post body does not have. The 'node_groups'
        # field in the response body is something like this
        #
        #   'node_groups': [
        #       {
        #           'count': 3,
        #           'name': 'worker-node',
        #           'volume_mount_prefix': '/volumes/disk',
        #           'created_at': '2014-05-21 14:31:37',
        #           'updated_at': None,
        #           'floating_ip_pool': None,
        #           ...
        #       },
        #       ...
        #   ]
        cls.cluster_template = cls.full_cluster_template.copy()
        del cls.cluster_template['node_groups']

    def _create_cluster_template(self, template_name=None):
        """Creates Cluster Template with optional name specified.

        It creates template, ensures template name and response body.
        Returns id and name of created template.
        """
        if not template_name:
            # generate random name if it's not specified
            template_name = data_utils.rand_name('sahara-cluster-template')

        # hack the arguments: keep the compatibility with the signature
        # of self.create_cluster_template
        full_cluster_template_w = self.full_cluster_template.copy()
        if 'plugin_version' in full_cluster_template_w:
            plugin_version_value = full_cluster_template_w['plugin_version']
            del full_cluster_template_w['plugin_version']
            full_cluster_template_w['hadoop_version'] = plugin_version_value

        # create cluster template
        resp_body = self.create_cluster_template(template_name,
                                                 **full_cluster_template_w)

        # ensure that template created successfully
        self.assertEqual(template_name, resp_body['name'])
        self.assertDictContainsSubset(self.cluster_template, resp_body)

        return resp_body['id'], template_name

    @tc.attr('smoke')
    @decorators.idempotent_id('3525f1f1-3f9c-407d-891a-a996237e728b')
    def test_cluster_template_create(self):
        self._create_cluster_template()

    @tc.attr('smoke')
    @decorators.idempotent_id('7a161882-e430-4840-a1c6-1d928201fab2')
    def test_cluster_template_list(self):
        template_info = self._create_cluster_template()

        # check for cluster template in list
        templates = self.client.list_cluster_templates()['cluster_templates']
        templates_info = [(template['id'], template['name'])
                          for template in templates]
        self.assertIn(template_info, templates_info)

    @tc.attr('smoke')
    @decorators.idempotent_id('2b75fe22-f731-4b0f-84f1-89ab25f86637')
    def test_cluster_template_get(self):
        template_id, template_name = self._create_cluster_template()

        # check cluster template fetch by id
        template = self.client.get_cluster_template(template_id)
        template = template['cluster_template']
        self.assertEqual(template_name, template['name'])
        self.assertDictContainsSubset(self.cluster_template, template)

    @tc.attr('smoke')
    @decorators.idempotent_id('ff1fd989-171c-4dd7-91fd-9fbc71b09675')
    def test_cluster_template_delete(self):
        template_id, _ = self._create_cluster_template()

        # delete the cluster template by id
        self.client.delete_cluster_template(template_id)
        get_resource = self.client.get_cluster_template
        self.wait_for_resource_deletion(template_id, get_resource)

        templates = self.client.list_cluster_templates()['cluster_templates']
        templates_info = [template['id']
                          for template in templates]
        self.assertNotIn(template_id, templates_info)

    @tc.attr('smoke')
    @decorators.idempotent_id('40235aa0-cd4b-494a-9c12-2d0e8a92157a')
    def test_cluster_template_update(self):
        template_id, _ = self._create_cluster_template()

        new_template_name = data_utils.rand_name('sahara-cluster-template')
        body = {'name': new_template_name}
        updated_template = self.client.update_cluster_template(template_id,
                                                               **body)
        updated_template = updated_template['cluster_template']

        self.assertEqual(new_template_name, updated_template['name'])
