import json
import os
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Dict
from urllib import request


@dataclass
class ActionContext:
    author: str
    access_token: str
    pipeline: str
    branch: str
    commit: str
    message: str
    env: Dict[str, str]
    is_async: bool

    @staticmethod
    def from_env(env: Dict[str, str]) -> "ActionContext":
        return ActionContext(
            author=env["GITHUB_ACTOR"],
            access_token=env["INPUT_ACCESS_TOKEN"],
            pipeline=env["INPUT_PIPELINE"],
            branch=env["INPUT_BRANCH"],
            commit=env["INPUT_COMMIT"],
            message=env["INPUT_MESSAGE"],
            env=json.loads(env.get("INPUT_ENV") or "{}"),
            is_async=env.get("INPUT_ASYNC", "false").lower() == "true"
        )


def main():
    context = ActionContext.from_env(os.environ)

    print(f"🪁 Triggering {context.pipeline} for {context.branch}@{context.commit}")
    build_info = trigger_pipeline(context)
    print(f"🔗 Build started: {build_info['web_url']}")

    state = "started"  # pseudo-state for async builds
    if not context.is_async:
        build_info = wait_for_build(build_info["url"], access_token=context.access_token)
        state = build_info["state"]

    print(f"::set-output name=id::{build_info['id']}")
    print(f"::set-output name=number::{build_info['number']}")
    print(f"::set-output name=url::{build_info['url']}")
    print(f"::set-output name=web_url::{build_info['web_url']}")
    print(f"::set-output name=state::{state}")
    print(f"::set-output name=data::{json.dumps(build_info)}")

    if state not in ["started", "passed"]:
        raise RuntimeError(f"Build failed with state {state}")


def trigger_pipeline(context: ActionContext) -> dict:
    url = pipeline_url(context.pipeline)
    headers = {"Authorization": f"Bearer {context.access_token}"}
    payload = {
        "commit": context.commit,
        "branch": context.branch,
        "message": context.message,
        "author": {
            "name": context.author
        },
        "env": context.env
    }
    data = bytes(json.dumps(payload), encoding="utf-8")
    req = request.Request(url, method="POST", headers=headers, data=data)
    res = request.urlopen(req, timeout=10)
    return json.loads(res.read())


def wait_for_build(url: str, *, access_token: str) -> dict:
    headers = {"Authorization": f"Bearer {access_token}"}
    req = request.Request(url, method="GET", headers=headers)
    last_status = datetime.now()
    finished_at = None
    data = {}
    print(f"⌛ Waiting for build to finish")
    while not finished_at:
        time.sleep(15)
        if (datetime.now() - last_status).total_seconds() > 60:
            print(f"⌛ Still waiting for build to finish")
            last_status = datetime.now()
        res = request.urlopen(req, timeout=10)
        data = json.loads(res.read())
        finished_at = data["finished_at"]
    return data


def pipeline_url(pipeline: str) -> str:
    organization, pipeline = pipeline.split("/", maxsplit=1)
    if (not organization) or (not pipeline) or ("/" in pipeline):
        raise ValueError("pipeline must be in the form 'organization/pipeline'")
    return f"https://api.buildkite.com/v2/organizations/{organization}/pipelines/{pipeline}/builds"


if __name__ == "__main__":
    main()
