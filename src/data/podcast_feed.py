"""Pydantic objects to describe a podcast feed."""

from typing import Optional, Union, List, Tuple

from pydantic import Field
from steamship.base.model import CamelModel
from steamship.data import TagKind
from steamship.data.tags.tag_constants import TagValueKey
from data.podcast_episode import RssEpisode, EpisodeFile
from data.utils import xmlify

from typing import Optional, Union, List, Tuple, cast

from steamship import File, Steamship, Block, Tag, DocTag, SteamshipError


class RssFeed(CamelModel):
    """Pydantic object that represents an RSS Feed."""

    guid: Optional[str] = Field(None, description="GUID of the feed.")
    title: Optional[str] = Field(None, description="Name of the feed.")
    web_url: Optional[str] = Field(None, description="Web URL of the feed.")
    language: Optional[str] = Field(None, description="Language of the feed.")
    copyright: Optional[str] = Field(None, description="Copyright text of the feed.")
    author: Optional[str] = Field(None, description="Author text of the feed.")
    summary: Optional[str] = Field(None, description="Summary text of the feed.")
    image_url: Optional[str] = Field(None, description="Image URL of the feed art.")
    category: Optional[str] = Field(None, description="Content category of the feed.")
    is_explicit: Optional[bool] = Field(None, description="Whether the feed is explicit")

    def rss_xml(self, base_url: str, episodes: Optional[List[RssEpisode]] = None):
        """Return the RSS feed."""

        ret = """<?xml version="1.0" encoding="UTF-8"?>
            <rss xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd" version="2.0">
            <channel>"""

        ret += xmlify([
            (self.title, "title", None, None),
            (self.author, "author", None, None),
            (self.author, "itunes:author", None, None),
            (self.summary, "description", None, None),
            (self.summary, "itunes:summary", None, None),
            (self.image_url, "itunes:image", "href", None),
            (self.web_url, "link", None, None),
            (self.language, "language", None, None),
            (self.copyright, "copyright", None, None),
            (self.is_explicit, "itunes:explicit", None, None),
            (self.category, "itunes:category", None, None),
        ])

        for episode in episodes:
            ret += episode.rss_xml(base_url=base_url)

        ret += "</channel></rss>"
        return ret

class FeedFile:
    """Wrapper object that helps store an RSS Feed on a Steamship File."""

    file: File
    TAG_KIND = "feed"
    TAG_GUID_KIND = "feed-guid"

    def __init__(self, file: File):
        self.file = file

    def to_rss(self, base_url: str, episode_files: List[EpisodeFile]) -> str:
        """Returns the RSS for this feed."""
        feed = self.feed_obj()
        episodes = [file.episode_obj() for file in episode_files]
        xml = feed.rss_xml(base_url, episodes)
        return xml

    def feed_tag(self) -> Optional[Tag]:
        """Returns the file tag that stores the feed metadata."""
        for tag in self.file.tags or []:
            if tag.kind == FeedFile.TAG_KIND:
                return tag
        return None

    def feed_obj(self) -> RssFeed:
        """Returns the Feed object stored in this file."""
        tag = self.feed_tag()
        if tag is not None:
            return RssFeed.parse_obj(tag.value)
        return RssFeed()

    @staticmethod
    def create(
        client: Steamship,
        base_url: str,
        rss_feed: Optional[RssFeed] = None,
    ) -> "FeedFile":
        # Only allow one per workspace
        files = File.query(client, f'filetag and kind "{FeedFile.TAG_KIND}"')
        if files and files.files and len(files.files) > 0:
            raise SteamshipError("This package is designed to host only one Podcast feed per workspace.")

        rss_feed = rss_feed or RssFeed()

        blocks = []
        blocks.append(Block(text="This file represents a podcast feed."))

        tags = [Tag(kind=FeedFile.TAG_KIND, value=rss_feed.dict())]
        if rss_feed and rss_feed.guid:
            tags.append(Tag(kind=FeedFile.TAG_GUID_KIND, name=rss_feed.guid))
        if rss_feed and rss_feed.title:
            tags.append(Tag(kind=TagKind.DOCUMENT, name=DocTag.TITLE, value={TagValueKey.STRING_VALUE: rss_feed.guid}))

        file = File.create(
            client,
            blocks=blocks,
            tags=tags
        )

        return FeedFile(file=file)

    @staticmethod
    def get_or_create(client: Steamship, base_url: str, rss_feed: Optional[RssFeed] = None,) -> "FeedFile":
        query = f'filetag and kind "{FeedFile.TAG_KIND}"'
        if rss_feed and rss_feed.guid:
            query = f'filetag and kind "{FeedFile.TAG_GUID_KIND}" and name "{rss_feed.guid}"'

        files = File.query(client, query)
        if files and files.files and len(files.files) > 0:
            return FeedFile(files.files[0])
        else:
            return FeedFile.create(client, base_url=base_url, rss_feed=rss_feed)
