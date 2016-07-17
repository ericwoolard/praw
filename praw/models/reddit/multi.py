"""Provide the Multireddit class."""
from json import dumps
import re

from ...const import API_PATH
from ..listing.mixins import SubredditListingMixin
from .base import RedditBase
from .redditor import Redditor
from .subreddit import Subreddit


class Multireddit(RedditBase, SubredditListingMixin):
    """A class for users' Multireddits."""

    STR_FIELD = 'path'
    RE_INVALID = re.compile('(\s|\W|_)+', re.UNICODE)

    @staticmethod
    def sluggify(title):
        """Return a slug version of the title.

        :param title: The title to make a slug of.

        Adapted from reddit's utils.py.

        """
        title = Multireddit.RE_INVALID.sub('_', title).strip('_').lower()
        if len(title) > 21:  # truncate to nearest word
            title = title[:21]
            last_word = title.rfind('_')
            if (last_word > 0):
                title = title[:last_word]
        return title or "_"

    def __init__(self, reddit, _data):
        """Construct an instance of the Multireddit object."""
        super(Multireddit, self).__init__(reddit, _data)
        self._author = Redditor(reddit, self.path.split('/', 3)[2])
        self._path = API_PATH['multireddit'].format(
            multi=self.name, user=self._author)
        self.path = '/' + self._path[:-1]  # Prevent requests for path
        if 'subreddits' in self.__dict__:
            self.subreddits = [Subreddit(reddit, x['name'])
                               for x in self.subreddits]

    def _info_path(self):
        return API_PATH['multireddit_about'].format(multi=self.name,
                                                    user=self._author)

    def add(self, subreddit):
        """Add a subreddit to this multireddit.

        :param subreddit: The subreddit to add to this multi.

        """
        url = API_PATH['multireddit_update'].format(
            multi=self.name, user=self._author, subreddit=subreddit)
        self._reddit.request(
            'put', url, data={'model': dumps({'name': str(subreddit)})})
        self._reset_attributes('subreddits')

    def copy(self, display_name=None):
        """Copy this multireddit and return the new multireddit.

        :param display_name: (optional) The display name for the copied
            multireddit. Reddit will generate the ``name`` field from this
            display name. When not provided the copy will use the same display
            name and name as this multireddit.

        """
        if display_name:
            name = self.sluggify(display_name)
        else:
            display_name = self.display_name
            name = self.name
        data = {'display_name': display_name, 'from': self.path,
                'to': API_PATH['multireddit'].format(
                    multi=name, user=self._reddit.user.me())}
        return self._reddit.post(API_PATH['multireddit_copy'], data=data)

    def delete(self):
        """Delete this multireddit."""
        self._reddit.request('delete', API_PATH['multireddit_about'].format(
            multi=self.name, user=self._author))

    def edit(self, *args, **kwargs):
        """Edit this multireddit.

        Convenience function that utilizes
        :meth:`.MultiredditMixin.edit_multireddit` populating the `name`
        parameter.

        """
        return self._reddit.edit_multireddit(name=self.name, *args, **kwargs)

    def remove(self, subreddit):
        """Remove a subreddit from this multireddit.

        :param subreddit: The subreddit to remove from this multi.

        """
        url = API_PATH['multireddit_update'].format(
            multi=self.name, user=self._author, subreddit=subreddit)
        self._reddit.request(
            'delete', url, data={'model': dumps({'name': str(subreddit)})})
        self._reset_attributes('subreddits')

    def rename(self, display_name):
        """Rename this multireddit.

        :param display_name: The new display name for this multireddit. Reddit
            will generate the ``name`` field from this display name.

        """
        data = {'from': self.path, 'display_name': display_name}
        updated = self._reddit.post(API_PATH['multireddit_rename'], data=data)
        self.__dict__.update(updated.__dict__)
