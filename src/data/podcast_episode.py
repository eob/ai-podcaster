"""Pydantic objects to describe a podcast feed."""

from typing import Optional, Union, List, Tuple, cast

from steamship import File, Steamship, Block, Tag, DocTag, SteamshipError
from steamship.data import TagKind, TagValueKey

from pydantic import Field
from steamship.base.model import CamelModel

from data.utils import xmlify


class RssEpisode(CamelModel):
    """Pydantic object that represents an RSS <item> object."""

    guid: Optional[str] = Field(None, description="GUID of the episode.")
    title: Optional[str] = Field(None, description="Name of the episode.")
    summary: Optional[str] = Field(None, description="Summary of the episode.")
    author: Optional[str] = Field(None, description="Summary of the episode.")
    web_url: Optional[str] = Field(None, description="Web URL of the episode audio.")
    audio_url: Optional[str] = Field(None, description="Audio URL of the episode audio.")
    is_explicit: Optional[bool] = Field(None, description="Whether the episode is explicit")
    pub_date: Optional[str] = Field(None, description="When the episode was published")

    def rss_xml(self, base_url: str) -> str:
        """Return the RSS <item> element for this object."""
        ret = "<item>"

        audio_url = self.audio_url or f"{base_url}audio?id={self.guid}"

        is_explicit_value = None
        if self.is_explicit is True:
            is_explicit_value = "yes"
        elif self.is_explicit is False:
            is_explicit_value = "no"

        ret += xmlify([
            (self.title, "title", None, None),
            (self.author, "author", None, None),
            (self.author, "itunes:author", None, None),
            (self.summary, "description", None, None),
            (self.summary, "itunes:summary", None, None),
            (audio_url, "enclosure", "url", "type=\"audio/mpeg\""),
            (self.guid, "guid", None, None),
            (is_explicit_value, "itunes:explicit", None, None),
            (self.pub_date, "pubDate", None, None),
        ])

        ret += "</item>"
        return ret


class EpisodeFile:
    """Wrapper object that helps store an RSS Episode on a Steamship File."""

    file: File

    TAG_KIND = "episode"
    TAG_NAME_AUDIO = "has_audio"
    TAG_NAME_DATA = "data"

    def __init__(self, file: File):
        self.file = file

    def mark_audio_complete(self) -> Optional[Tag]:
        """Returns the file tag that stores the episode metadata."""
        return Tag.create(
            self.file.client,
            file_id=self.file.id,
            kind=EpisodeFile.TAG_KIND,
            name=EpisodeFile.TAG_NAME_AUDIO
        )

    def episode_tag(self) -> Optional[Tag]:
        """Returns the file tag that stores the episode metadata."""
        for tag in self.file.tags or []:
            if tag.kind == EpisodeFile.TAG_KIND and tag.name == EpisodeFile.TAG_NAME_DATA:
                return tag
        return None

    def episode_obj(self) -> RssEpisode:
        """Returns the Episode object stored in this file."""
        tag = self.episode_tag()
        if tag is not None:
            ep = RssEpisode.parse_obj(tag.value)
        else:
            ep = RssEpisode()

        ep.guid = self.file.id
        return ep

    @staticmethod
    def list(client: Steamship, with_audio: Optional[bool] == None) -> "List[EpisodeFile]":
        if with_audio is True:
            files = File.query(client, f'filetag and kind "{EpisodeFile.TAG_KIND}" and name "{EpisodeFile.TAG_NAME_AUDIO}"')
        else:
            files = File.query(client, f'filetag and kind "{EpisodeFile.TAG_KIND}" and name "{EpisodeFile.TAG_NAME_DATA}"')
        return [EpisodeFile(file) for file in files.files or []]

    @staticmethod
    def get(client: Steamship, id: str) -> "EpisodeFile":
        file = File.get(client, _id=id)
        return EpisodeFile(file)

    @staticmethod
    def create(
        client: Steamship,
        rss_episode: Optional[RssEpisode] = None,
        content: Optional[Union[str, List[str]]] = "Episode Content",
    ) -> "EpisodeFile":
        blocks = []

        if rss_episode.title:
            blocks.append(Block(
                text=rss_episode.title,
                tags=[Tag(kind=TagKind.DOCUMENT, name=DocTag.TITLE)]
            ))

        if rss_episode.author:
            blocks.append(Block(
                text=f"By {rss_episode.author}",
                tags=[Tag(kind=TagKind.DOCUMENT, name=DocTag.H2)]
            ))

        if type(content) == str:
            content = [content]

        for text in content:
            blocks.append(
                Block(
                    text=text,
                    tags=[Tag(kind=TagKind.DOCUMENT, name=DocTag.TEXT)]
                )
            )

        file = File.create(
            client,
            blocks=blocks,
            tags=[Tag(kind=EpisodeFile.TAG_KIND, name=EpisodeFile.TAG_NAME_DATA, value=rss_episode.dict())]
        )
        return EpisodeFile(file=file)


