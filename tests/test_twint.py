import os
import unittest

from lib.Twint import temporary_tweet_csv_path


class TemporaryTweetCsvPathTest(unittest.TestCase):

  def test_overlapping_searches_use_isolated_paths_and_clean_up(self):
    with temporary_tweet_csv_path() as first_path:
      first_directory = os.path.dirname(first_path)
      with temporary_tweet_csv_path() as second_path:
        second_directory = os.path.dirname(second_path)
        self.assertNotEqual(first_path, second_path)
        self.assertTrue(os.path.isdir(first_directory))
        self.assertTrue(os.path.isdir(second_directory))

        with open(first_path, 'w') as first_file:
          first_file.write('first')
        with open(second_path, 'w') as second_file:
          second_file.write('second')

      self.assertFalse(os.path.exists(second_directory))
      self.assertTrue(os.path.exists(first_path))

    self.assertFalse(os.path.exists(first_directory))


if __name__ == '__main__':
  unittest.main()
