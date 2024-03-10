const { getToken } = require('./utils/tokenManager');
// TODO: Move Token management + Axios configuration to a single configuration util
const axios = require('axios');
const API_ENDPOINT = process.env.API_URL;
axios.defaults.baseURL = API_ENDPOINT;
axios.defaults.headers.common['Content-Type'] = 'application/json';
axios.defaults.headers.common['LANG'] = 'ar'

// Check number
// Subscribtions/GetSubscribtion {PhoneNumber}
async function GetSubscription(phoneNumber) {
    try {
      const token = await getToken();
      const endpoint = "Subscribtions/GetSubscribtion";
      const headers = {
        'Authorization': `Bearer ${token}`
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
      const endpoint = "Subscribtions/CheckSubscription";
      const headers = {
        'Authorization': `Bearer ${token}`
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
// TODO: add error handling in case the phoneNumber is not valid
async function getSubscriptionDetails(phoneNumber) {
    try {
      const getSubscription = await GetSubscription(phoneNumber);
      const number = getSubscription[0].number;
      const startDate = getSubscription[0].startDate;
      const endDate = getSubscription[0].endDate;
        
      
      const checkSubscription = await CheckSubscription(phoneNumber);
      const usage = {
        "voiceUsed": checkSubscription.voice_Used,
        "voiceSize": checkSubscription.voice_Size,
        "messagesUsed": checkSubscription.messages_Used,
        "messagesSize": checkSubscription.messages_Size,
        "internetUsed": checkSubscription.internet_UsedMB,
        "internetSize": checkSubscription.internet_Size,
        "packageUsage": checkSubscription.package_Usage
      };
      checkSubscription.package_Usage;
      const isActive = checkSubscription.number.status === 'فعال'
      
      const res = {
        "number": number,
        "startDate": startDate,
        "endDate": endDate,
        "isActive": isActive,
        "usage": usage
      };
      
      return res
  } catch (error) {
    console.error('Error Getting Number Status:', error);
    return null;
  }
}

async function extendSubscription(phoneNumber, isWithSale = false) {
    try {
      let Duration;
      let SaleId;
      if (isWithSale) {
        const sales = await getSales(phoneNumber)
        SaleId = sales[0].id;
      }
      else{
        Duration = 30;
      }
      
      const token = await getToken();
      const endpoint = "Deals/Extend";
      const headers = {
        'Authorization': `Bearer ${token}`
      };
      const payload = {
        Number: phoneNumber,
        Duration: Duration,
        SaleId: SaleId,
        UserPaid: true
      };
      const response = await axios.post(endpoint, payload,
                                        {headers: headers});
      const data = response.data;
      return data
  } catch (error) {
    console.error('Error Extending the subscription:', error);
    return null;
  }
};

async function activateSubscription(phoneNumber, isWithSale = true) {
    try {
      let Duration;
      let SaleId;
      if (isWithSale) {
        const sales = await getSales(phoneNumber)
        SaleId = sales[0].id;
      }
      else {
        Duration = 30;
      }
      
      const token = await getToken();
      const endpoint = "Deals/ActivateLine";
      const headers = {
        'Authorization': `Bearer ${token}`
      };
      const payload = {
        Number: phoneNumber,
        Duration: Duration,
        SaleId: SaleId,
        UserPaid: true
      };
      const response = await axios.post(endpoint, payload,
                                        {headers: headers});
      
      const data = response.data;
      return data
  } catch (error) {
    console.error('Error activating the subscription:', error);
    return null;
  }
};

async function getSales(phoneNumber) {
    try {
      const token = await getToken();
      const endpoint = "Subscribtions/GetSalesByNumber/" + phoneNumber;
      const headers = {
        'Authorization': `Bearer ${token}`
      };
      const response = await axios.get(endpoint,
                                       {headers: headers});
      const data = response.data;
      return data
  } catch (error) {
    console.error('Error getting sales:', error);
    return null;
  }
};

module.exports = { getSubscriptionDetails, extendSubscription, activateSubscription };
