# Copyright 2014-2015 Canonical Ltd.  This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

"""Tests for the `Boot Source Selections` API."""

from __future__ import (
    absolute_import,
    print_function,
    unicode_literals,
    )

str = None

__metaclass__ = type
__all__ = []

import httplib
import json

from django.core.urlresolvers import reverse
from maasserver.api.boot_source_selections import (
    DISPLAYED_BOOTSOURCESELECTION_FIELDS,
)
from maasserver.models import BootSourceSelection
from maasserver.models.testing import UpdateBootSourceCacheDisconnected
from maasserver.testing.api import APITestCase
from maasserver.testing.factory import factory
from maasserver.testing.orm import reload_object
from testtools.matchers import MatchesStructure


def get_boot_source_selection_uri(boot_source_selection):
    """Return a boot source's URI on the API."""
    boot_source = boot_source_selection.boot_source
    return reverse(
        'boot_source_selection_handler',
        args=[
            boot_source.id,
            boot_source_selection.id,
        ]
    )


def get_boot_source_selection_backward_uri(
        boot_source_selection, nodegroup=None):
    """Return a boot source's URI on the API."""
    if nodegroup is None:
        nodegroup = factory.make_NodeGroup()
    boot_source = boot_source_selection.boot_source
    return reverse(
        'boot_source_selection_backward_handler',
        args=[
            nodegroup.uuid,
            boot_source.id,
            boot_source_selection.id,
        ]
    )


class TestBootSourceSelectionAPI(APITestCase):

    def setUp(self):
        super(TestBootSourceSelectionAPI, self).setUp()
        self.useFixture(UpdateBootSourceCacheDisconnected())

    def test_handler_path(self):
        self.assertEqual(
            '/api/1.0/boot-sources/3/selections/4/',
            reverse(
                'boot_source_selection_handler',
                args=['3', '4']))

    def test_GET_returns_boot_source(self):
        self.become_admin()
        boot_source_selection = factory.make_BootSourceSelection()
        response = self.client.get(
            get_boot_source_selection_uri(boot_source_selection))
        self.assertEqual(httplib.OK, response.status_code)
        returned_boot_source_selection = json.loads(response.content)
        boot_source = boot_source_selection.boot_source
        # The returned object contains a 'resource_uri' field.
        self.assertEqual(
            reverse(
                'boot_source_selection_handler',
                args=[
                    boot_source.id,
                    boot_source_selection.id]
            ),
            returned_boot_source_selection['resource_uri'])
        # The other fields are the boot source selection's fields.
        del returned_boot_source_selection['resource_uri']
        # All the fields are present.
        self.assertItemsEqual(
            DISPLAYED_BOOTSOURCESELECTION_FIELDS,
            returned_boot_source_selection.keys())
        self.assertThat(
            boot_source_selection,
            MatchesStructure.byEquality(**returned_boot_source_selection))

    def test_GET_requires_admin(self):
        boot_source_selection = factory.make_BootSourceSelection()
        response = self.client.get(
            get_boot_source_selection_uri(boot_source_selection))
        self.assertEqual(httplib.FORBIDDEN, response.status_code)

    def test_DELETE_deletes_boot_source_selection(self):
        self.become_admin()
        boot_source_selection = factory.make_BootSourceSelection()
        response = self.client.delete(
            get_boot_source_selection_uri(boot_source_selection))
        self.assertEqual(httplib.NO_CONTENT, response.status_code)
        self.assertIsNone(reload_object(boot_source_selection))

    def test_DELETE_requires_admin(self):
        boot_source_selection = factory.make_BootSourceSelection()
        response = self.client.delete(
            get_boot_source_selection_uri(boot_source_selection))
        self.assertEqual(httplib.FORBIDDEN, response.status_code)

    def test_PUT_updates_boot_source_selection(self):
        self.become_admin()
        boot_source_selection = factory.make_BootSourceSelection()
        new_os = factory.make_name('os')
        new_release = factory.make_name('release')
        boot_source_caches = factory.make_many_BootSourceCaches(
            2, boot_source=boot_source_selection.boot_source, os=new_os,
            release=new_release)
        new_values = {
            'os': new_os,
            'release': new_release,
            'arches': [boot_source_caches[0].arch, boot_source_caches[1].arch],
            'subarches': [
                boot_source_caches[0].subarch, boot_source_caches[1].subarch],
            'labels': [boot_source_caches[0].label],
        }
        response = self.client.put(
            get_boot_source_selection_uri(boot_source_selection), new_values)
        self.assertEqual(httplib.OK, response.status_code, response.content)
        boot_source_selection = reload_object(boot_source_selection)
        self.assertAttributes(boot_source_selection, new_values)

    def test_PUT_requires_admin(self):
        boot_source_selection = factory.make_BootSourceSelection()
        new_values = {
            'release': factory.make_name('release'),
        }
        response = self.client.put(
            get_boot_source_selection_uri(boot_source_selection), new_values)
        self.assertEqual(httplib.FORBIDDEN, response.status_code)


class TestBootSourceSelectionBackwardAPI(APITestCase):

    def setUp(self):
        super(TestBootSourceSelectionBackwardAPI, self).setUp()
        self.useFixture(UpdateBootSourceCacheDisconnected())

    def test_handler_path(self):
        self.assertEqual(
            '/api/1.0/nodegroups/uuid/boot-sources/3/selections/4/',
            reverse(
                'boot_source_selection_backward_handler',
                args=['uuid', '3', '4']))

    def test_GET_returns_boot_source(self):
        self.become_admin()
        boot_source_selection = factory.make_BootSourceSelection()
        response = self.client.get(
            get_boot_source_selection_backward_uri(boot_source_selection))
        self.assertEqual(httplib.OK, response.status_code)
        returned_boot_source_selection = json.loads(response.content)
        boot_source = boot_source_selection.boot_source
        # The returned object contains a 'resource_uri' field.
        self.assertEqual(
            reverse(
                'boot_source_selection_handler',
                args=[
                    boot_source.id,
                    boot_source_selection.id]
            ),
            returned_boot_source_selection['resource_uri'])
        # The other fields are the boot source selection's fields.
        del returned_boot_source_selection['resource_uri']
        # All the fields are present.
        self.assertItemsEqual(
            DISPLAYED_BOOTSOURCESELECTION_FIELDS,
            returned_boot_source_selection.keys())
        self.assertThat(
            boot_source_selection,
            MatchesStructure.byEquality(**returned_boot_source_selection))

    def test_GET_returns_same_boot_source_for_different_node_groups(self):
        self.become_admin()
        boot_source_selection = factory.make_BootSourceSelection()
        for _ in range(3):
            nodegroup = factory.make_NodeGroup()
            response = self.client.get(
                get_boot_source_selection_backward_uri(
                    boot_source_selection, nodegroup))
            self.assertEqual(httplib.OK, response.status_code)
            returned_boot_source_selection = json.loads(response.content)
            del returned_boot_source_selection['resource_uri']
            self.assertThat(
                boot_source_selection,
                MatchesStructure.byEquality(**returned_boot_source_selection))

    def test_GET_requires_admin(self):
        boot_source_selection = factory.make_BootSourceSelection()
        response = self.client.get(
            get_boot_source_selection_backward_uri(boot_source_selection))
        self.assertEqual(httplib.FORBIDDEN, response.status_code)

    def test_DELETE_deletes_boot_source_selection(self):
        self.become_admin()
        boot_source_selection = factory.make_BootSourceSelection()
        response = self.client.delete(
            get_boot_source_selection_backward_uri(boot_source_selection))
        self.assertEqual(httplib.NO_CONTENT, response.status_code)
        self.assertIsNone(reload_object(boot_source_selection))

    def test_DELETE_requires_admin(self):
        boot_source_selection = factory.make_BootSourceSelection()
        response = self.client.delete(
            get_boot_source_selection_backward_uri(boot_source_selection))
        self.assertEqual(httplib.FORBIDDEN, response.status_code)

    def test_PUT_updates_boot_source_selection(self):
        self.become_admin()
        boot_source_selection = factory.make_BootSourceSelection()
        new_release = factory.make_name('release')
        boot_source_caches = factory.make_many_BootSourceCaches(
            2, boot_source=boot_source_selection.boot_source,
            release=new_release)
        new_values = {
            'release': new_release,
            'arches': [boot_source_caches[0].arch, boot_source_caches[1].arch],
            'subarches': [
                boot_source_caches[0].subarch, boot_source_caches[1].subarch],
            'labels': [boot_source_caches[0].label],
        }
        response = self.client.put(
            get_boot_source_selection_backward_uri(
                boot_source_selection), new_values)
        self.assertEqual(httplib.OK, response.status_code)
        boot_source_selection = reload_object(boot_source_selection)
        self.assertAttributes(boot_source_selection, new_values)

    def test_PUT_requires_admin(self):
        boot_source_selection = factory.make_BootSourceSelection()
        new_values = {
            'release': factory.make_name('release'),
        }
        response = self.client.put(
            get_boot_source_selection_backward_uri(
                boot_source_selection), new_values)
        self.assertEqual(httplib.FORBIDDEN, response.status_code)


class TestBootSourceSelectionsAPI(APITestCase):
    """Test the the boot source selections API."""

    def setUp(self):
        super(TestBootSourceSelectionsAPI, self).setUp()
        self.useFixture(UpdateBootSourceCacheDisconnected())

    def test_handler_path(self):
        self.assertEqual(
            '/api/1.0/boot-sources/3/selections/',
            reverse('boot_source_selections_handler', args=['3']))

    def test_GET_returns_boot_source_selection_list(self):
        self.become_admin()
        boot_source = factory.make_BootSource()
        selections = [
            factory.make_BootSourceSelection(boot_source=boot_source)
            for _ in range(3)]
        # Create boot source selections in another boot source.
        [factory.make_BootSourceSelection() for _ in range(3)]
        response = self.client.get(
            reverse(
                'boot_source_selections_handler',
                args=[boot_source.id]))
        self.assertEqual(httplib.OK, response.status_code, response.content)
        parsed_result = json.loads(response.content)
        self.assertItemsEqual(
            [selection.id for selection in selections],
            [selection.get('id') for selection in parsed_result])

    def test_GET_requires_admin(self):
        boot_source = factory.make_BootSource()
        response = self.client.get(
            reverse(
                'boot_source_selections_handler',
                args=[boot_source.id]))
        self.assertEqual(httplib.FORBIDDEN, response.status_code)

    def test_POST_creates_boot_source_selection(self):
        self.become_admin()
        boot_source = factory.make_BootSource()
        new_release = factory.make_name('release')
        boot_source_caches = factory.make_many_BootSourceCaches(
            2, boot_source=boot_source,
            release=new_release)
        params = {
            'release': new_release,
            'arches': [boot_source_caches[0].arch, boot_source_caches[1].arch],
            'subarches': [
                boot_source_caches[0].subarch, boot_source_caches[1].subarch],
            'labels': [boot_source_caches[0].label],
        }
        response = self.client.post(
            reverse(
                'boot_source_selections_handler',
                args=[boot_source.id]), params)
        self.assertEqual(httplib.OK, response.status_code)
        parsed_result = json.loads(response.content)

        boot_source_selection = BootSourceSelection.objects.get(
            id=parsed_result['id'])
        self.assertAttributes(boot_source_selection, params)

    def test_POST_requires_admin(self):
        boot_source = factory.make_BootSource()
        new_release = factory.make_name('release')
        params = {
            'release': new_release,
            'arches': [factory.make_name('arch'), factory.make_name('arch')],
            'subarches': [
                factory.make_name('subarch'), factory.make_name('subarch')],
            'labels': [factory.make_name('label')],
        }
        response = self.client.post(
            reverse(
                'boot_source_selections_handler',
                args=[boot_source.id]), params)
        self.assertEqual(httplib.FORBIDDEN, response.status_code)


class TestBootSourceSelectionsBackwardAPI(APITestCase):
    """Test the the boot source selections API."""

    def setUp(self):
        super(TestBootSourceSelectionsBackwardAPI, self).setUp()
        self.useFixture(UpdateBootSourceCacheDisconnected())

    def get_uri(self, boot_source, nodegroup=None):
        if nodegroup is None:
            nodegroup = factory.make_NodeGroup()
        return reverse(
            'boot_source_selections_backward_handler',
            args=[nodegroup.uuid, boot_source.id])

    def test_handler_path(self):
        self.assertEqual(
            '/api/1.0/nodegroups/uuid/boot-sources/3/selections/',
            reverse(
                'boot_source_selections_backward_handler',
                args=['uuid', '3']))

    def test_GET_returns_boot_source_selection_list(self):
        self.become_admin()
        boot_source = factory.make_BootSource()
        selections = [
            factory.make_BootSourceSelection(boot_source=boot_source)
            for _ in range(3)]
        # Create boot source selections in another boot source.
        [factory.make_BootSourceSelection() for _ in range(3)]
        response = self.client.get(self.get_uri(boot_source))
        self.assertEqual(httplib.OK, response.status_code, response.content)
        parsed_result = json.loads(response.content)
        self.assertItemsEqual(
            [selection.id for selection in selections],
            [selection.get('id') for selection in parsed_result])

    def test_GET_returns_same_list_for_different_node_groups(self):
        self.become_admin()
        boot_source = factory.make_BootSource()
        selections = [
            factory.make_BootSourceSelection(boot_source=boot_source)
            for _ in range(3)]
        # Create boot source selections in another boot source.
        [factory.make_BootSourceSelection() for _ in range(3)]
        for _ in range(3):
            nodegroup = factory.make_NodeGroup()
            response = self.client.get(self.get_uri(boot_source, nodegroup))
            self.assertEqual(
                httplib.OK, response.status_code, response.content)
            parsed_result = json.loads(response.content)
            self.assertItemsEqual(
                [selection.id for selection in selections],
                [selection.get('id') for selection in parsed_result])

    def test_GET_requires_admin(self):
        boot_source = factory.make_BootSource()
        response = self.client.get(self.get_uri(boot_source))
        self.assertEqual(httplib.FORBIDDEN, response.status_code)

    def test_POST_creates_boot_source_selection(self):
        self.become_admin()
        boot_source = factory.make_BootSource()
        new_release = factory.make_name('release')
        boot_source_caches = factory.make_many_BootSourceCaches(
            2, boot_source=boot_source, release=new_release)
        params = {
            'release': new_release,
            'arches': [boot_source_caches[0].arch, boot_source_caches[1].arch],
            'subarches': [
                boot_source_caches[0].subarch, boot_source_caches[1].subarch],
            'labels': [boot_source_caches[0].label],
        }
        response = self.client.post(self.get_uri(boot_source), params)
        self.assertEqual(httplib.OK, response.status_code)
        parsed_result = json.loads(response.content)

        boot_source_selection = BootSourceSelection.objects.get(
            id=parsed_result['id'])
        self.assertAttributes(boot_source_selection, params)

    def test_POST_requires_admin(self):
        boot_source = factory.make_BootSource()
        new_release = factory.make_name('release')
        params = {
            'release': new_release,
            'arches': [factory.make_name('arch'), factory.make_name('arch')],
            'subarches': [
                factory.make_name('subarch'), factory.make_name('subarch')],
            'labels': [factory.make_name('label')],
        }
        response = self.client.post(self.get_uri(boot_source), params)
        self.assertEqual(httplib.FORBIDDEN, response.status_code)
