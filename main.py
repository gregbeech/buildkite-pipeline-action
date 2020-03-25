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
    is_test_mode: bool

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
            is_async=env.get("INPUT_ASYNC", "false").lower() == "true",
            is_test_mode=env.get("TEST_MODE", "false").lower() == "true",
        )


def main():
    context = ActionContext.from_env(os.environ)

    print(f"🪁 Triggering {context.pipeline} for {context.branch}@{context.commit}")
    build_info = trigger_pipeline(context)
    print(f"🔗 Build started → {build_info['web_url']}")

    if not context.is_async:
        build_info = wait_for_build(build_info["url"], context)

    state = build_info["state"]
    print(f"{state_emoji(state)} Build {state} → {build_info['web_url']}")

    print(f"::set-output name=id::{build_info['id']}")
    print(f"::set-output name=number::{build_info['number']}")
    print(f"::set-output name=url::{build_info['url']}")
    print(f"::set-output name=web_url::{build_info['web_url']}")
    print(f"::set-output name=state::{state}")
    print(f"::set-output name=data::{json.dumps(build_info)}")

    if state not in ["scheduled", "running", "passed"]:
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
    return http_send(req, context, test_response="create_build")


def wait_for_build(url: str, context: ActionContext) -> dict:
    headers = {"Authorization": f"Bearer {context.access_token}"}
    req = request.Request(url, method="GET", headers=headers)
    last_status = datetime.now()
    build_info = {}
    print(f"⌛ Waiting for build to finish")
    while not build_info.get("finished_at"):
        time.sleep(15)
        if (datetime.now() - last_status).total_seconds() > 60:
            print(f"⌛ Still waiting for build to finish")
            last_status = datetime.now()
        build_info = http_send(req, context, test_response="build_passed")
    return build_info


def pipeline_url(pipeline: str) -> str:
    organization, pipeline = pipeline.split("/", maxsplit=1)
    if (not organization) or (not pipeline) or ("/" in pipeline):
        raise ValueError("pipeline must be in the form 'organization/pipeline'")
    return f"https://api.buildkite.com/v2/organizations/{organization}/pipelines/{pipeline}/builds"


def state_emoji(state: str) -> str:
    return {
        "scheduled": "⏱️️",
        "running": "🏃",
        "passed": "💚",
    }.get(state, "💔")


def http_send(req: request.Request, context: ActionContext, *, test_response: str) -> dict:
    if context.is_test_mode:
        res = open(f"./test_responses/{test_response}.json", "rb")
    else:
        res = request.urlopen(req, timeout=10)
    return json.loads(res.read())


if __name__ == "__main__":
    main()
