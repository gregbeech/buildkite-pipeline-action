# Buildkite pipeline action

This action triggers a [https://buildkite.com/](Buildkite) pipeline and (by default) waits for it to finish.

## Why not use the official action?

The [official Buildkite action](https://github.com/buildkite/trigger-pipeline-action) appears to be abandoned as it hasn't had any changes in nearly a year, is missing essential functionality such as the ability to wait until a pipeline is finished, and has a number of bugs such as using the wrong branch name on `pull_request` events.

## Inputs

### `access_token`

**Required** A Buildkite access token which must have the `write_builds` permission, and if you want to wait for the builds to complete also needs the `read_builds` permission.

### `pipeline`

**Required** Name of the pipeline to trigger, in the format `organization/pipeline`.

### `branch`

**Required** Name of the branch to build. Default is the current branch.

### `commit`

**Required** The commit to build. Default is the current commit.

### `message`

**Required** The message to associate with the build. Default `":github: Triggered by GitHub Action"`.

### `env`

Environment variables to pass to the Buildkite build in JSON format. Note that this is distinct from the GitHub Actions `env` setting which passes environment variables to the action itself.

### `async`

If true then the action does not wait for the build to complete. Default `false`.

## Outputs

### `id`

The identifier of the build.

### `number`

The build number.

### `url`

The API URL of the build.

### `web_url`

The web URL of the build.

### `state`

The state of the build.

### `data`

The raw data about the build in JSON format.

## Example usage

```yaml
uses: zegocover/buildkite-pipeline-action@master
with:
  access_token: '${{ secrets.buildkite_access_token }}'
  pipeline: 'my-org/my-pipeline'
  message: ':github: Running my-pipeline for ${{ github.actor }}'
  env: '{"TARGET":"QA"}'
```
