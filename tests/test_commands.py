import pytest
from gidgethub.sansio import Event

from algorithms_keeper import commands

from .utils import (
    MockGitHubAPI,
    comment_url,
    files_url,
    html_pr_url,
    pr_url,
    reactions_url,
    user,
)


@pytest.mark.parametrize(
    "text",
    (
        "algorithms-keeper test",
        "@algorithm-keeper test",
        "@algorithms_keeper test",
        "@algorithms-keepertest test",
    ),
)
def test_command_regex_no_match(text):
    assert commands.COMMAND_RE.search(text) is None


@pytest.mark.parametrize(
    "text, group",
    (
        ("@algorithms-keeper test", "test"),
        ("@algorithms-keeper review", "review"),
        ("@algorithms-keeper      review     ", "review"),
        ("random @algorithms-keeper     review   random", "review"),
        ("@Algorithms-Keeper   REVIEW  ", "REVIEW"),
    ),
)
def test_command_regex_match(text, group):
    assert commands.COMMAND_RE.search(text).group(1) == group


@pytest.mark.asyncio
async def test_comment_by_non_member():
    data = {"action": "created", "comment": {"author_association": "NONE"}}
    event = Event(data, event="issue_comment", delivery_id="1")
    gh = MockGitHubAPI()
    await commands.router.dispatch(event, gh)
    assert not gh.post_url
    assert not gh.getitem_url
    assert not gh.delete_url


@pytest.mark.asyncio
async def test_comment_on_issue():
    data = {
        "action": "created",
        "comment": {
            "url": comment_url,
            "author_association": "MEMBER",
            "body": "@algorithms-keeper review",
        },
        "issue": {},
    }
    event = Event(data, event="issue_comment", delivery_id="1")
    post = {reactions_url: None}
    gh = MockGitHubAPI(post=post)
    await commands.router.dispatch(event, gh)
    assert len(gh.post_url) == 1
    assert reactions_url in gh.post_url
    assert {"content": "-1"} in gh.post_data
    assert not gh.getitem_url
    assert not gh.delete_url


@pytest.mark.asyncio
async def test_random_command():
    data = {
        "action": "created",
        "comment": {
            "author_association": "MEMBER",
            "body": "@algorithms-keeper random",
        },
    }
    event = Event(data, event="issue_comment", delivery_id="1")
    gh = MockGitHubAPI()
    await commands.router.dispatch(event, gh)
    assert not gh.post_url
    assert not gh.getitem_url
    assert not gh.getiter_url
    assert not gh.delete_url


@pytest.mark.asyncio
async def test_review_command():
    data = {
        "action": "created",
        "comment": {
            "url": comment_url,
            "author_association": "MEMBER",
            "body": "@algorithms-keeper review",
        },
        "issue": {"pull_request": {"url": pr_url}},
    }
    event = Event(data, event="issue_comment", delivery_id="1")
    post = {reactions_url: None}
    getitem = {
        pr_url: {
            "url": pr_url,
            "html_url": html_pr_url,
            "user": {"login": user},
            "labels": [],
            "draft": False,
        },
    }
    getiter = {files_url: []}
    gh = MockGitHubAPI(post=post, getitem=getitem, getiter=getiter)
    await commands.router.dispatch(event, gh)
    assert len(gh.post_url) == 1
    assert reactions_url in gh.post_url
    assert {"content": "+1"} in gh.post_data
    assert len(gh.getitem_url) == 1
    assert pr_url in gh.getitem_url
    assert len(gh.getiter_url) == 1
    assert files_url in gh.getiter_url
    assert not gh.delete_url
