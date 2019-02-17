var AWS = require('aws-sdk');
var s3 = new AWS.S3();
var http = require('http');
var request = require('request');

var imageUrl = "https://www.accc.gov.au/sites/default/files/fuelwatch/brisbane-ulp.png";

var s3bucket = new AWS.S3();
var bucketName = "accc-fuel-images";

exports.handler = (event, context) => {
    var formattedDate = new Date().toISOString().slice(0, 10);

    request(imageUrl, { encoding: 'binary'}, (error, response, body) => {
        var params = {
            Bucket: bucketName,
            Key: "brisbane/" + formattedDate + ".png",
            Body: new Buffer(body, 'binary'),
        };

        s3.putObject(params, (err, data) => {
            if (err) console.log(err, err.stack);
            else     console.log(data);
            context.done(null, 'Finished UploadObjectOnS3');
        });
    });
};