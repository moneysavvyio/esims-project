# Layan-T Slack Client

Slack client to interact with [Layan-T](https://www.layan-t.net) functionality.
View, extend, and activate subscriptions from within Slack.

## Configuration
Configure the following environment variables:
```
- SLACK_BOT_TOKEN
- SLACK_SIGNING_SECRET
- LAYANT_USERNAME
- LAYANT_PASSWORD
- JWT_FILEPATH
- API_URL=https://api.layan-t.net/api/
```
And run
`npm start`

Then, go to https://api.slack.com/apps and install the app.

Configure the Request URLs to be the base URL of the web server + `/slack/events`

Example:
`https://example.com/slack/events`

## Usage

`/wecom <number>`

To get the details of a subscription and prompt an extension or activation.
