const AWS = require('aws-sdk');
const dynamodb = new AWS.DynamoDB({ region: 'ap-southeast-2' });

const supportedCombos = [
  'adelaide/ulp',
  'brisbane/ulp',
  'melbourne/ulp',
  'perth/ulp',
  'sydney/e10',
];

const hasInvalidPath = (path) => {
  if (!path.startsWith('/v1/')) {
    return true;
  }

  const pathParts = path.slice(4).split('/');
  if (!pathParts.length === 3) {
    return true;
  }

  if (!supportedCombos.includes(pathParts.slice(0, 2).join('/'))) {
    return true;
  }

  const date = pathParts[2];
  if (!/^\d{4}-\d{2}-\d{2}$/.test(date)) {
    return true;
  }
  return false;
}

exports.handler = (event) => {
  const path = event.path;
  if (hasInvalidPath(path)) {
    return Promise.resolve({
      statusCode: 400,
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        error: "Invalid path, should be '/v1/{city}/{fuel-type}/{iso-date}'.",
        details: `Supported {city}/{fuel-type} combos: ${supportedCombos.join(', ')}`
      }),
    })
  }

  return dynamodb.getItem({
    Key: { "RegionFuelDate": { S: path.slice(4) } },
    TableName: "accc-fuel-data"
   }).promise()
    .then(data => data.Item ? parseFloat(data.Item.Cost.N) : null)
    .then(cost => ({
      statusCode: cost == null ? 404 : 200,
      headers: { "Content-Type": "application/json" },
      body: cost == null ? '{}' : JSON.stringify({ cost }),
    }))
    .catch(e => console.error(e) || {
      statusCode: 400,
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ error: e.message }),
    });
}
