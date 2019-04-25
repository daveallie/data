const AWS = require('aws-sdk');
const s3 = new AWS.S3();
const request = require('request');
const bucketName = "accc-fuel-images-2";

const fuelImageUrls = {
  'adelaide/ulp': 'https://www.accc.gov.au/sites/www.accc.gov.au/files/fuelwatch/adelaide-ulp.png',
  'brisbane/ulp': 'https://www.accc.gov.au/sites/www.accc.gov.au/files/fuelwatch/brisbane-ulp.png',
  'melbourne/ulp': 'https://www.accc.gov.au/sites/www.accc.gov.au/files/fuelwatch/melbourne-ulp.png',
  'perth/ulp': 'https://www.accc.gov.au/sites/www.accc.gov.au/files/fuelwatch/perth-ulp.png',
  'sydney/e10': 'https://www.accc.gov.au/sites/www.accc.gov.au/files/fuelwatch/sydney-e10.png',
};

exports.handler = (event) => {
  const year = new Date().getFullYear();
  const formattedDate = new Date().toISOString().slice(0, 10);

  return Promise.all(
    Object.entries(fuelImageUrls).map(([key, url]) =>
      new Promise(resolve =>
        request(url, { encoding: "binary" }, (error, response, body) =>
          s3.putObject({
            Bucket: bucketName,
            Key: key + "/" + year + "/" + formattedDate + ".png",
            Body: new Buffer(body, "binary"),
          },
          () => resolve())
        )
      )
    )
  );
};
