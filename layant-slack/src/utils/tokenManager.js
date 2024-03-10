const fs = require('fs').promises;
const jwt = require('jsonwebtoken');
const axios = require('axios');
const API_ENDPOINT = process.env.API_URL;
axios.defaults.baseURL = API_ENDPOINT;
axios.defaults.headers.common['Content-Type'] = 'application/json';
axios.defaults.headers.common['LANG'] = 'ar';

// TODO: Move the token to a secret store in production
const TOKEN_PATH = process.env.JWT_FILEPATH;

const USERNAME = process.env.LAYANT_USERNAME;
const PASSWORD = process.env.LAYANT_PASSWORD;
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
    const response = await axios.post("Auth/Login", {
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
    // console.log('No token found, refreshing...');
    return await refreshToken();
  }

  const payload = jwt.decode(token);

  if (!payload || !payload.exp || Date.now() >= payload.exp * 1000) {
    console.log('Token expired or invalid, refreshing...');
    return await refreshToken();
  }

  // console.log('Token is valid, proceeding with existing token.');
  return token;
}


module.exports = { getToken };