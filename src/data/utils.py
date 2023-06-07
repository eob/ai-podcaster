"""Pydantic objects to describe a podcast feed."""

from typing import Optional, Union, List, Tuple

from pydantic import Field
from steamship.base.model import CamelModel

def xmlify(values: List[Tuple[str, str, Optional[str], Optional[str]]]) -> str:
    "Turn a list of values into XML elements. The tuple is: value, tagname, attname"
    ret = ""
    for value, tag_name, attribute_name, extras in values:
        if extras is None:
            extras = ""
        if value is not None:
            if attribute_name is not None:
                ret += f"<{tag_name} {attribute_name}=\"{value}\" {extras} />"
            else:
                ret += f"<{tag_name} {extras}>{value}</{tag_name}>"
    return ret


class Episode(CamelModel):
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


class Feed(CamelModel):
    """Pydantic object that represents an RSS Feed."""

    title: Optional[str] = Field(None, description="Name of the feed.")
    web_url: Optional[str] = Field(None, description="Web URL of the feed.")
    language: Optional[str] = Field(None, description="Language of the feed.")
    copyright: Optional[str] = Field(None, description="Copyright text of the feed.")
    author: Optional[str] = Field(None, description="Author text of the feed.")
    summary: Optional[str] = Field(None, description="Summary text of the feed.")
    image_url: Optional[str] = Field(None, description="Image URL of the feed art.")
    category: Optional[str] = Field(None, description="Content category of the feed.")
    is_explicit: Optional[bool] = Field(None, description="Whether the feed is explicit")

    def rss_xml(self, base_url: str, episodes: Optional[List[Episode]] = None):
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

