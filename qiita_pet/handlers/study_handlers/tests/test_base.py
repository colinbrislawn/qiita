# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------
from unittest import main
from json import loads

from qiita_pet.test.tornado_test_base import TestHandlerBase


class StudyIndexHandlerTests(TestHandlerBase):
    def test_get_exists(self):
        response = self.get('/study/description/1')
        self.assertEqual(response.code, 200)

    def test_get_no_exists(self):
        response = self.get('/study/description/245')
        self.assertEqual(response.code, 404)


class StudyBaseInfoAJAX(TestHandlerBase):
    # TODO: Missing tests
    pass


class StudyDeleteAjaxTests(TestHandlerBase):
    database = True

    def test_delete_study(self):
        response = self.post('/study/delete/', {'study_id': 1})
        self.assertEqual(response.code, 200)
        exp = {'status': 'error',
               'message': 'Unable to delete study: Study "Identification of '
                          'the Microbiomes for Cannabis Soils" cannot be '
                          'erased because it has a sample template'}
        self.assertEqual(loads(response.body), exp)

if __name__ == "__main__":
    main()