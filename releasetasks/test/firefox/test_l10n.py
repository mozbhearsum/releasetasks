import unittest

from releasetasks.test.firefox import make_task_graph, get_task_by_name, \
    do_common_assertions
from releasetasks.test import PVT_KEY_FILE
from releasetasks.test.firefox import create_firefox_test_args
from voluptuous import Schema


class TestL10NSingleChunk(unittest.TestCase):
    maxDiff = 30000
    graph = None
    task = None
    payload = None
    properties = None

    TASK_SCHEMA = Schema({
        'task': {
            'provisionerId': 'buildbot-bridge',
            'workerType': 'buildbot-bridge',
            'payload': {
                'properties': {
                    'repo_path': 'releases/mozilla-beta',
                    'script_repo_revision': 'abcd',
                    'builderName': 'release-mozilla-beta_firefox_win32_l10n_repack',
                    'locales': 'de:default en-GB:default zh-TW:default',
                    'en_us_binary_url': 'https://queue.taskcluster.net/something/firefox.exe',
                }
            }
        }
    })

    def setUp(self):
        test_arguments = create_firefox_test_args({
            'updates_enabled': True,
            'signing_pvt_key': PVT_KEY_FILE,
            'branch': "mozilla-beta",
            'repo_path': "releases/mozilla-beta",
            'release_channels': ["beta"],
            'final_verify_channels': ["beta"],

            'en_US_config': {
                "platforms": {
                    "win32": {
                        "task_id": "xyy"
                    }
                }
            },
            'l10n_config': {
                "platforms": {
                    "win32": {
                        "en_us_binary_url": "https://queue.taskcluster.net/something/firefox.exe",
                        "locales": ["de", "en-GB", "zh-TW"],
                        "chunks": 1,
                    },
                    "linux64": {
                        "en_us_binary_url": "https://queue.taskcluster.net/something/firefox.tar.xz",
                        "locales": ["de", "en-GB", "zh-TW"],
                        "chunks": 1,
                    },

                },
                "changesets": {
                    "de": "default",
                    "en-GB": "default",
                    "zh-TW": "default",
                }
            },
        })
        self.graph = make_task_graph(**test_arguments)
        self.task = get_task_by_name(self.graph, "release-mozilla-beta_firefox_win32_l10n_repack_1")
        self.payload = self.task["task"]["payload"]
        self.properties = self.payload["properties"]

    def test_common_assertions(self):
        do_common_assertions(self.graph)

    def test_task_present(self):
        self.assertIsNotNone(self.task)

    def test_only_one_chunk_1(self):
        self.assertIsNone(get_task_by_name(self.graph, "release-mozilla-beta_firefox_win32_l10n_repack_0"))

    def test_only_one_chunk_2(self):
        self.assertIsNone(get_task_by_name(self.graph, "release-mozilla-beta_firefox_win32_l10n_repack_2"))

    def test_artifacts_task_present(self):
        self.assertIsNotNone(get_task_by_name(self.graph, "release-mozilla-beta_firefox_win32_l10n_repack_artifacts_1"))

    def test_artifacts_task_only_one_chunk_1(self):
        self.assertIsNone(get_task_by_name(self.graph, "release-mozilla-beta_firefox_win32_l10n_repack_artifacts_0"))

    def test_artifacts_task_only_one_chunk_2(self):
        self.assertIsNone(get_task_by_name(self.graph, "release-mozilla-beta_firefox_win32_l10n_repack_artifacts_2"))

    def test_artifacts_task_provisioner(self):
        art_task = get_task_by_name(self.graph, "release-mozilla-beta_firefox_win32_l10n_repack_artifacts_1")
        self.assertEqual(art_task["task"]["provisionerId"], "null-provisioner")

    def test_artifacts_task_worker_type(self):
        art_task = get_task_by_name(self.graph, "release-mozilla-beta_firefox_win32_l10n_repack_artifacts_1")
        self.assertEqual(art_task["task"]["workerType"], "buildbot")

    def test_partials_present(self):
        for pl in ["win32", "linux64"]:
            for part in ["37.0", "38.0"]:
                task_name = "release-mozilla-beta_firefox_{pl}_l10n_repack_1_{part}_update_generator".format(
                    pl=pl, part=part)
                self.assertIsNotNone(get_task_by_name(
                    self.graph, task_name))

    def test_funsize_name(self):
        for platform in ("win32", "linux64",):
            for version in ("37.0", "38.0",):
                generator = get_task_by_name(self.graph,
                                             "release-mozilla-beta_firefox_{pl}_l10n_repack_1_{part}_update_generator".format(pl=platform, part=version))
                signing = get_task_by_name(self.graph,
                                           "release-mozilla-beta_firefox_{pl}_l10n_repack_1_{part}_signing_task".format(pl=platform, part=version))
                balrog = get_task_by_name(self.graph,
                                          "release-mozilla-beta_firefox_{pl}_l10n_repack_1_{part}_balrog_task".format(pl=platform, part=version))
                self.assertEqual(generator["task"]["metadata"]["name"],
                                 "[funsize] Update generating task %s chunk %s for %s" % (platform, "1", version,))
                self.assertEqual(signing["task"]["metadata"]["name"],
                                 "[funsize] MAR signing task %s chunk %s for %s" % (platform, "1", version,))
                self.assertEqual(balrog["task"]["metadata"]["name"],
                                 "[funsize] Publish to Balrog %s chunk %s for %s" % (platform, "1", version,))


class TestL10NMultipleChunks(unittest.TestCase):
    maxDiff = 30000
    graph = None
    chunk1 = None
    chunk2 = None
    chunk1_properties = None
    chunk2_properties = None

    def setUp(self):
        self.chunk1_schema = Schema({
            'task': {
                'payload': {
                    'builderName': 'release-mozilla-beta_firefox_win32_l10n_repack',
                    'locales': 'de:default en-GB:default ru:default',
                    'en_us_binary_url': 'https://queue.taskcluster.net/something/firefox.exe',
                    'repo_path': 'releases/mozilla-beta',
                    'script_repo_revision': 'abcd',
                }
            }
        })

        self.chunk2_schema = Schema({
            'task': {
                'payload': {
                    'builderName': 'release-mozilla-beta_firefox_win32_l10n_repack',
                    'locales': 'uk:default zh-TW:default',
                    'en_us_binary_url': 'https://queue.taskcluster.net/something/firefox.exe',
                    'repo_path': 'releases/mozilla-beta',
                    'script_repo_revision': 'abcd'
                }
            }
        })
        test_kwargs = create_firefox_test_args({
            'updates_enabled': True,
            'repo_path': 'releases/mozilla-beta',
            'branch': 'mozilla-beta',
            'signing_pvt_key': PVT_KEY_FILE,
            'release_channels': ['beta'],
            'final_verify_channels': ['beta'],
            'en_US_platforms': ['win32'],
            'en_US_config': {
                "platforms": {
                    "win32": {"task_id": "xyy"}
                }
            },
            'l10n_config': {
                "platforms": {
                    "win32": {
                        "en_us_binary_url": "https://queue.taskcluster.net/something/firefox.exe",
                        "locales": ["de", "en-GB", "ru", "uk", "zh-TW"],
                        "chunks": 2,
                    },
                    "linux64": {
                        "en_us_binary_url": "https://queue.taskcluster.net/something/firefox.tar.xz",
                        "locales": ["de", "en-GB", "ru", "uk", "zh-TW"],
                        "chunks": 2,
                    },
                },
                "changesets": {
                    "de": "default",
                    "en-GB": "default",
                    "ru": "default",
                    "uk": "default",
                    "zh-TW": "default",
                },
            },
        })
        self.graph = make_task_graph(**test_kwargs)
        self.chunk1 = get_task_by_name(
            self.graph, "release-mozilla-beta_firefox_win32_l10n_repack_1")
        self.chunk2 = get_task_by_name(
            self.graph, "release-mozilla-beta_firefox_win32_l10n_repack_2")
        self.chunk1_properties = self.chunk1["task"]["payload"]["properties"]
        self.chunk2_properties = self.chunk2["task"]["payload"]["properties"]

    def test_common_assertions(self):
        do_common_assertions(self.graph)

    def test_chunk2_script_repo_revision(self):
        self.assertEqual(self.chunk2_properties["script_repo_revision"],
                         "abcd")

    def test_no_chunk3(self):
        self.assertIsNone(get_task_by_name(
            self.graph, "release-mozilla-beta_firefox_win32_l10n_repack_3"))

    def test_chunk1_artifacts_task_present(self):
        # make sure artifacts tasks are present
        self.assertIsNotNone(get_task_by_name(
            self.graph,
            "release-mozilla-beta_firefox_win32_l10n_repack_artifacts_1"))

    def test_chunk2_artifacts_task_present(self):
        self.assertIsNotNone(get_task_by_name(
            self.graph,
            "release-mozilla-beta_firefox_win32_l10n_repack_artifacts_2"))

    def test_no_chunk3_artifacts(self):
        self.assertIsNone(get_task_by_name(
            self.graph,
            "release-mozilla-beta_firefox_win32_l10n_repack_artifacts_3"))

    def test_partials_present(self):
        for pl in ["win32", "linux64"]:
            for part in ["37.0", "38.0"]:
                for chunk in [1, 2]:
                    task_name1 = "release-mozilla-beta_firefox_{pl}_l10n_repack_{chunk}_{part}_update_generator".format(
                        pl=pl, part=part, chunk=chunk)
                    task_name2 = "release-mozilla-beta_firefox_{pl}_l10n_repack_{chunk}_{part}_signing_task".format(
                        pl=pl, part=part, chunk=chunk)
                    self.assertIsNotNone(get_task_by_name(
                        self.graph, task_name1))
                    self.assertIsNotNone(get_task_by_name(
                        self.graph, task_name2))

    def test_funsize_name(self):
        for platform in ("win32", "linux64",):
            for version in ("37.0", "38.0",):
                for chunk in ('1', '2',):
                    generator = get_task_by_name(self.graph,
                                                 "release-mozilla-beta_firefox_{pl}_l10n_repack_{c}_{part}_update_generator".format(
                                                     pl=platform, part=version, c=chunk))
                    signing = get_task_by_name(self.graph,
                                               "release-mozilla-beta_firefox_{pl}_l10n_repack_{c}_{part}_signing_task".format(
                                                   pl=platform, part=version, c=chunk))
                    balrog = get_task_by_name(self.graph,
                                              "release-mozilla-beta_firefox_{pl}_l10n_repack_{c}_{part}_balrog_task".format(
                                                  pl=platform, part=version, c=chunk))
                    self.assertEqual(generator["task"]["metadata"]["name"],
                                     "[funsize] Update generating task %s chunk %s for %s" % (platform, chunk, version,))
                    self.assertEqual(signing["task"]["metadata"]["name"],
                                     "[funsize] MAR signing task %s chunk %s for %s" % (platform, chunk, version,))
                    self.assertEqual(balrog["task"]["metadata"]["name"],
                                     "[funsize] Publish to Balrog %s chunk %s for %s" % (platform, chunk, version,))


class TestL10NNewLocales(unittest.TestCase):
    maxDiff = 30000
    graph = None

    def setUp(self):
        test_kwargs = create_firefox_test_args({
            'updates_enabled': True,
            'push_to_candidates_enabled': True,
            'branch': 'mozilla-beta',
            'repo_path': 'releases/mozilla-beta',
            'signing_pvt_key': PVT_KEY_FILE,
            'release_channels': ['beta'],
            'final_verify_channels': ['beta'],
            'enUS_platforms': ['win32'],
            'en_US_config': {
                "platforms": {
                    "win32": {"task_id": "xyy"}
                }
            },
            'l10n_config': {
                "platforms": {
                    "win32": {
                        "en_us_binary_url": "https://queue.taskcluster.net/something/firefox.exe",
                        "locales": ["de", "en-GB", "ru", "uk", "zh-TW"],
                        "chunks": 1,
                    },
                    "linux64": {
                        "en_us_binary_url": "https://queue.taskcluster.net/something/firefox.tar.xz",
                        "locales": ["de", "en-GB", "ru", "uk", "zh-TW"],
                        "chunks": 1,
                    },
                },
                "changesets": {
                    "de": "default",
                    "en-GB": "default",
                    "ru": "default",
                    "uk": "default",
                    "zh-TW": "default",
                },
            },
            'partial_updates': {
                '38.0': {
                    'buildNumber': 1,
                    'locales': [
                        'de', 'en-GB', 'ru', 'uk', 'zh-TW'
                    ]
                },
                '37.0': {
                    'buildNumber': 2,
                    'locales': [
                        'de', 'en-GB', 'ru', 'uk'
                    ]
                }
            }
        })
        self.graph = make_task_graph(**test_kwargs)

    def test_common_assertions(self):
        do_common_assertions(self.graph)

    def test_new_locale_not_in_update_generator(self):
        t = get_task_by_name(
            self.graph,
            "release-mozilla-beta_firefox_win32_l10n_repack_1_37.0_update_generator")
        self.assertEqual(
            sorted(["de", "en-GB", "ru", "uk"]),
            sorted([p["locale"] for p in t["task"]["extra"]["funsize"]["partials"]]))

    def test_new_locale_in_update_generator(self):
        t = get_task_by_name(
            self.graph,
            "release-mozilla-beta_firefox_win32_l10n_repack_1_38.0_update_generator")
        self.assertEqual(sorted(["de", "en-GB", "ru", "uk", "zh-TW"]),
                         sorted([p["locale"] for p in t["task"]["extra"]["funsize"]["partials"]]))

    def test_new_locale_not_in_beetmover(self):
        t = get_task_by_name(
            self.graph,
            "release-mozilla-beta_firefox_win32_l10n_repack_partial_37.0build2_beetmover_candidates_1")
        self.assertNotIn("--locale zh-TW",  " ".join(t["task"]["payload"]["command"]))
        self.assertIn("--locale en-GB", " ".join(t["task"]["payload"]["command"]))

    def test_new_locale_in_beetmover(self):
        t = get_task_by_name(
            self.graph,
            "release-mozilla-beta_firefox_win32_l10n_repack_partial_38.0build1_beetmover_candidates_1")
        self.assertIn("--locale zh-TW", " ".join(t["task"]["payload"]["command"]))
        self.assertIn("--locale en-GB", " ".join(t["task"]["payload"]["command"]))
