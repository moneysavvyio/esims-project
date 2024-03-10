// TODO: Add tests
// TODO: Configure a logger and logging service
// TODO: Add success and error notifications to an admin channel
// TODO: Get prices dynamically from API calls (or at least have them as global environment variables)
// TODO: Add option for the user to choose betwen using the sale and the regular package

const { App } = require("@slack/bolt");

const { getSlackFormattedDate, addDaysAndFormat } = require('./utils/dateTime');
const { getSubscriptionDetails, extendSubscription, activateSubscription, getSales } = require('./layan-t-api');

const app = new App({
  token: process.env.SLACK_BOT_TOKEN,
  signingSecret: process.env.SLACK_SIGNING_SECRET,
});

app.command('/wecom', async ({ command, ack, respond, body, client, context}) => {
  await ack({
    text: "Processing your request, please wait...",
    response_type: "ephemeral"
  });

  const phoneNumber = command.text.trim();
  try {
    
    
    const subscriptionDetails = await getSubscriptionDetails(phoneNumber);
    // console.log(subscriptionDetails);
    
    await respond(
      {
      response_type: "ephemeral",
      text: "Subscription Details",
      
      blocks: [
        {
          "type": "section",
          "text": {
            "type": "mrkdwn",
            "text": "*Subscription*"
          }
        },
        
        {
          "type": "section",
          "fields": [
            {
              "type": "mrkdwn",
              "text": `*Number:*\n${subscriptionDetails.number}`
            },
            {
              "type": "mrkdwn",
              "text": `*Usage:*\n ${subscriptionDetails.usage.internetUsed} GB data\n${subscriptionDetails.usage.voiceUsed} calls\n${subscriptionDetails.usage.messagesUsed} messages`
            },
            {
              "type": "mrkdwn",
              "text": `*Start:*\n${getSlackFormattedDate(subscriptionDetails.startDate)}`
            },
            {
              "type": "mrkdwn",
              "text": `*Expiration:*\n${getSlackFormattedDate(subscriptionDetails.endDate)}`
            },
            {
              "type": "mrkdwn",
              "text": `*Status:*\n ${subscriptionDetails.isActive ? 'Active ✅' : 'Inactive ❌'}`
            }
          ]
        },
        
        // Conditionally render an 'Activate' or 'Extend' button        
        subscriptionDetails.isActive ?
        {
          type: 'actions',
          elements: [
            {
              type: 'button',
              text: {
                type: 'plain_text',
                text: 'Extend'
                // text: subscriptionDetails.isActive ? 'Extend' : 'Activate',
              },
              style: 'primary',
              value: JSON.stringify(subscriptionDetails),
              action_id: 'request_extend_subscription',
            },
          ],
        } 
        
        :
        // if the subscription is expired, render an 'Activate' button   
        {
          type: 'actions',
          elements: [
            {
              type: 'button',
              text: {
                type: 'plain_text',
                text: 'Activate',
              },
              style: 'primary',
              // pass the subscription object in the value field
              value: JSON.stringify(subscriptionDetails),
              action_id: 'request_activate_subscription',
            },
          ],
        }
      ]
    }
    )
    
  } catch (error) {
    console.error(error);
    await respond({
      response_type: "ephemeral",
      text: 'An error occurred. Please ensure that the phone number you entered is a valid Wecom number'
    });
  }
});


app.action('request_extend_subscription', async ({ body, ack, client }) => {
  await ack();
  const stringified_subscription = body.actions[0].value
  const subscription = JSON.parse(stringified_subscription);
  
  // TODO: Get these numbers dynamically from Layan-T API calls
  const costInShekels = 30;  
  const duration = 30;


  const view = await client.views.open({
    trigger_id: body.trigger_id,
    view: {
    callback_id: "confirm_extend_subscription",
    //  Pass the subscription as private_metadata
    private_metadata: stringified_subscription,
    "type": "modal",
    "title": {
      "type": "plain_text",
      "text": "Extend " + subscription.number + "?"
    },
    "submit": {
      "type": "plain_text",
      "text": "Extend",
      "emoji": true
    },
    "close": {
      "type": "plain_text",
      "text": "Do Nothing",
      "emoji": true
    },
    "blocks": [
      {
        "type": "section",
        "fields": [
          {
            "type": "mrkdwn",
            "text": `*Current Expiration Date:*\n${getSlackFormattedDate(subscription.endDate)}`
          },
          {
            "type": "mrkdwn",
            "text": `*Duration:*\n${duration} days`
          },
          {
            "type": "mrkdwn",
            "text": `*New Expiration Date:*\n${getSlackFormattedDate(addDaysAndFormat(subscription.endDate, duration))}`
          },
          {
            "type": "mrkdwn",
            "text": `*Cost:*\n ₪ ${costInShekels}`
          }
        ]
      }
    ]
  }  
  });
});

app.view('confirm_extend_subscription', async ({ ack, body, view, client }) => {
  await ack();
  
  const stringified_subscription = view.private_metadata;
  const subscription = JSON.parse(stringified_subscription);
  
  try {
      await client.chat.postEphemeral({
        channel: body.user.id,
        user: body.user.id,
        text: "Processing extension request..."
      })
    
    const res = await extendSubscription(subscription.number);
    console.log("res:", res)
    
    await client.chat.postEphemeral({
        channel: body.user.id,
        user: body.user.id,
        text: "Subscription extended successfully ✅. The changes will be reflected shortly."
      })
    
    //     TODO: Post the result to an admin notifications channel
    // await client.chat.postMessage({
    //   channel: user,
    //   text: msg
    // });
                                      
  }
  catch (error) {
    console.error(error);
  }
});


app.action('request_activate_subscription', async ({ body, ack, client }) => {
  // Acknowledge the button click event
  await ack();
  const stringified_subscription = body.actions[0].value
  const subscription = JSON.parse(stringified_subscription);
  
  // TODO: Get these values dynamically from API calls to Layan-T
  const activationCostInShekels = 79;
  const duration = 90;


  // Open a confirmation modal
  const view = await client.views.open({
    trigger_id: body.trigger_id,
    view: {
    callback_id: "confirm_activate_subscription",
    private_metadata: stringified_subscription,
    "type": "modal",
    "title": {
      "type": "plain_text",
      "text": "Activate " + subscription.number + "?"
    },
    "submit": {
      "type": "plain_text",
      "text": "Activate",
      "emoji": true
    },
    "close": {
      "type": "plain_text",
      "text": "Do Nothing",
      "emoji": true
    },
    "blocks": [
      {
        "type": "section",
        "fields": [
          {
            "type": "mrkdwn",
            "text": `*Current Expiration Date:*\n${getSlackFormattedDate(subscription.endDate)}`
          },
          {
            "type": "mrkdwn",
            "text": `*Duration:*\n${duration} days`
          },
          {
            "type": "mrkdwn",
            "text": `*New Expiration Date:*\n${getSlackFormattedDate(addDaysAndFormat(subscription.endDate, duration))}`
          },
          {
            "type": "mrkdwn",
            "text": `*Cost:*\n ₪ ${activationCostInShekels}`
          }
        ]
      }
    ]
  }  
  });
});


app.view('confirm_activate_subscription', async ({ ack, body, view, client }) => {
  await ack();
  
  const stringified_subscription = view.private_metadata;
  const subscription = JSON.parse(stringified_subscription);
  
  try {
      await client.chat.postEphemeral({
        channel: body.user.id,
        user: body.user.id,
        text: "Processing activation request..."
      })
    
    const res = await activateSubscription(subscription.number);
    console.log("res:", res)
    
    await client.chat.postEphemeral({
        channel: body.user.id,
        user: body.user.id,
        text: "Subscription activated successfully ✅ The changes will be reflected shortly."
      })
    
    //     TODO: Post the result to a channel
    // await client.chat.postMessage({
    //   channel: user,
    //   text: msg
    // });
                                      
  }
  catch (error) {
    console.error(error);
  }
});


(async () => {
  // Start your app
  await app.start(process.env.PORT || 3000);
  console.log("⚡️ Bolt app is running");  
}
)();
