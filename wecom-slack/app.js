// Require the Bolt package (github.com/slackapi/bolt)
const { App } = require("@slack/bolt");
const fs = require('fs').promises;
const jwt = require('jsonwebtoken');
const axios = require('axios');

const app = new App({
  token: process.env.SLACK_BOT_TOKEN,
  signingSecret: process.env.SLACK_SIGNING_SECRET,
});

// The echo command simply echoes on command
app.command('/check', async ({ command, ack, respond }) => {
  // Acknowledge command request
  await ack();
  await respond("Fetching...");
  
  try {
    const numberStatus = await GetNumberStatus(command.text);
    await respond(`*Wecom number*: ${numberStatus.number}\n*Start Date*:  ${numberStatus.startDate}\n*Expiration Date*:  ${numberStatus.endDate}
    \nUsage: ${numberStatus.usagePercentage}%`);
    
  } catch (error) {
    console.error('Error Getting number data:', error);
    await respond(`Error getting information for ${command.text}. Please ensure it is a valid wecom number`);
  }

  
});

const TOKEN_PATH = process.env.JWT_FILEPATH;
const API_ENDPOINT = process.env.API_URL;
const USERNAME = process.env.USERNAME;
const PASSWORD = process.env.PASSWORD;

// Function to read the token from file
async function readTokenFromFile() {
  try {
    return await fs.readFile(TOKEN_PATH, 'utf8');
  } catch (error) {
    console.error('Error reading the token from file:', error);
    return null;
  }
}

// Function to save the token to file
async function saveTokenToFile(token) {
  try {
    await fs.writeFile(TOKEN_PATH, token, 'utf8');
  } catch (error) {
    console.error('Error saving the token to file:', error);
  }
}

// Function to refresh the token
async function refreshToken() {
  try {
    const response = await axios.post(API_ENDPOINT + "Auth/Login", {
      username: USERNAME,
      password: PASSWORD,
    });
    const token = response.data.data.jwt;
    await saveTokenToFile(token);
    return token;
  } catch (error) {
    console.error('Error refreshing the token:', error);
    return null;
  }
}

// Main function to get a valid token, refreshing it if necessary
async function getToken() {
  let token = await readTokenFromFile();
  
  if (!token) {
    console.log('No token found, refreshing...');
    return await refreshToken();
  }

  const payload = jwt.decode(token);

  if (!payload || !payload.exp || Date.now() >= payload.exp * 1000) {
    console.log('Token expired or invalid, refreshing...');
    return await refreshToken();
  }

  console.log('Token is valid, proceeding with existing token.');
  return token;
}

// Check number
// Subscribtions/GetSubscribtion {PhoneNumber} (expiration date)
async function GetSubscription(phoneNumber) {
    try {
      const token = await getToken();
      const endpoint = API_ENDPOINT + "Subscribtions/GetSubscribtion";
      const headers = {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json', // Ensure to set the content type for JSON payload
        'LANG': 'ar'
      };
      const payload = {
        PhoneNumber: phoneNumber
      };
      const response = await axios.post(endpoint, payload,
                                        {headers: headers});
      const data = response.data;
      return data
  } catch (error) {
    console.error('Error in GetSubscription :', error);
    return null;
  }
}

// Subscribtions/CheckSubscription {Number} (usage data)
async function CheckSubscription(phoneNumber) {
    // internet_Size
    // internet_UsedMB
    // messages_Used
    // messages_Size
    // voice_Used
    // voice_Size
    // externalVoiceUsed
    // externalVoiceSize
    // package_Usage
    try {
      const token = await getToken();
      const endpoint = API_ENDPOINT + "Subscribtions/CheckSubscription";
      const headers = {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json', // Ensure to set the content type for JSON payload
        'LANG': 'ar'
      };
      const payload = {
        Number: phoneNumber
      };
      const response = await axios.post(endpoint, payload,
                                        {headers: headers});
      const data = response.data;
      return data
  } catch (error) {
    console.error('Error in CheckSubscription:', error);
    return null;
  }
}


// Get number status
// number, startDate, expDate, usage data
async function GetNumberStatus(phoneNumber) {
    try {
      const getSubscription = await GetSubscription(phoneNumber);
      const checkSubscription = await CheckSubscription(phoneNumber);
      
      const res = {
        "number": getSubscription[0].number,
        "startDate": getSubscription[0].startDate,
        "endDate": getSubscription[0].endDate,
        "usagePercentage": checkSubscription.package_Usage
      }
      return res
  } catch (error) {
    console.error('Error Getting Number Status:', error);
    return null;
  }
}

// Get the expiration date
async function getNumberExpirationDate(phoneNumber) {
    try {
      const phoneNumberStatus = await GetSubscription(phoneNumber);
      return phoneNumberStatus[0].endDate;
  } catch (error) {
    console.error('Error Getting the number expiration date :', error);
    return null;
  }
}

// "Subscribtions/RenewSubscribtion/" + phoneNumber
async function renewSubscription(phoneNumber) {
    try {
      const token = await getToken();
      const endpoint = API_ENDPOINT + "Subscribtions/RenewSubscribtion/" + phoneNumber;
      const headers = {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json', // Ensure to set the content type for JSON payload
        'LANG': 'ar'
      };
      const payload = {
//         empty
      };
      const response = await axios.post(endpoint, payload,
                                        {headers: headers});
      const data = response.data;
      return data
  } catch (error) {
    console.error('Error Getting the number status :', error);
    return null;
  }
};

// Renew a number only if the expiration date is no later than 7 days from today
async function renewIfExpiring(phoneNumber) {
  try {
    const expirationDateString = await getNumberExpirationDate(phoneNumber);
    // Parse the date string "DD/MM/YYYY HH:mm" into a Date object
    const [day, month, year, hour, minute] = expirationDateString.split(/[/ :]/);
    const expirationDate = new Date(year, month - 1, day, hour, minute); // Note: months are 0-based
    const currentDate = new Date();
    const sevenDaysLater = new Date(currentDate.getTime() + 7 * 24 * 60 * 60 * 1000);

    if (isNaN(expirationDate.getTime())) {
      throw new Error('Invalid expiration date format.');
    }

    if (expirationDate <= sevenDaysLater) {
      // Expiration date is within the next 7 days or in the past, proceed with renewal
      await renewSubscription(phoneNumber);
      return `Subscription for ${phoneNumber} renewed successfully.`;
    } else {
      // Expiration date is more than 7 days away, throw an error
      throw new Error(`Subscription for ${phoneNumber} does not need renewal at this time.`);
    }
  } catch (error) {
    // Handle or rethrow the error as needed
    throw new Error(`Error processing renewal for ${phoneNumber}: ${error.message}`);
  }
}

(async () => {
  // Start your app
  await app.start(process.env.PORT || 3000);

  console.log("⚡️ Bolt app is running");

}
)();
