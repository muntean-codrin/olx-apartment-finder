const { ActivityType } = require('discord.js');
const mysql = require('mysql2');
const client = require('..');
const chalk = require('chalk');

client.on("ready", () => {
	console.log(chalk.red(`Logged in as ${client.user.tag}`))
	const activities = [
		{ name: `chirii in Cluj-Napoca`, type: ActivityType.Watching }
	];
	
	let connection = mysql.createConnection({
		host: 'localhost',
		user: 'root',
		password: 'test',
		database: 'olx_scrape'
	});
	
	
	sendRent("garsoniera", "cluj-napoca", "1364572685824426045", connection)
	sendRent("2camere", "cluj-napoca", "1364572713448112178", connection)
	
	let i = 0;
	setInterval(() => {
		if(i >= activities.length) i = 0
		client.user.setActivity(activities[i])
		i++;
	}, 5000);
});


function sendRent(type, city, channel, connection){
	let query = `SELECT * FROM listings WHERE sent = 0 AND type='${type}'`;
	setInterval(() => {
		connection.connect();
		connection.query(query, function (err, rows, fields) {
			if (err) throw err;
			for(let i=0;i<rows.length;i++){
				connection.query(`UPDATE listings SET sent = 1 WHERE id = ${rows[i].id}`, (error, results, fields) => {
					if (error){
					  return console.error(error.message);
					}
				});
				const userId = "351987352584978434";
				let startOfMessage = rows[i].reactualizat ? "♻️ Reactualizat" : "🆕 Nou:";

				let message = `**${startOfMessage} - <@${userId}>- ${rows[i].title.charAt(0).toUpperCase() + rows[i].title.slice(1)}** 🗺️\n> Pret: ${rows[i].price}\n> Locatie: ${rows[i].location}\n> Data postare: ${rows[i].date}, ${rows[i].time}\n> **Link: ${rows[i].link}**`;
				console.log(`🏠 Sending listing id=${rows[i].id} - ${rows[i].title}`);
				client.channels.cache.get(channel).send(message);
			}
		});
	}, 60*10)
}