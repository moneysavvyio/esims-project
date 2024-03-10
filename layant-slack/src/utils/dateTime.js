const moment = require('moment-timezone');

function toUnixEpoch(dateString, format="DD/MM/YYYY HH:mm", timezone="Asia/Jerusalem"){
  return moment.tz(dateString, format, timezone).unix();
}
function getSlackFormattedDate(dateString, format="DD/MM/YYYY HH:mm", timezone="Asia/Jerusalem"){
  return `<!date^${toUnixEpoch(dateString, format, timezone)}^{date_short_pretty} {time}|${dateString} (Jerusalem)>`
}
function addDaysAndFormat(dateString, numDays, format="DD/MM/YYYY HH:mm", timezone="Asia/Jerusalem") {
    return moment.tz(dateString, format, timezone).add(numDays, 'days').format(format);
}
// Export the functions
module.exports = { toUnixEpoch, getSlackFormattedDate, addDaysAndFormat };
