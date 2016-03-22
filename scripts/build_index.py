import datetime
import os
from os.path import join

def build_index_for_feed(feed_dict):
	feed_dir = feed_dict['feed_dir']

	crawl_name = feed_dict['crawl_name']
	crawl_type = feed_dict['crawl_type']
	short_name = feed_dict['short_name']

	header_types = {'mentions':'Twitter Mentions','hashtag':'Tweets','user':'Tweets'}
	header_text = crawl_name + ' ' + header_types[crawl_type]

	index = join(feed_dir, 'index.html')

	html_dir = join(feed_dir, 'html')
	json_dir = join(feed_dir, 'json')

	table_rows = ""
	for filename in os.listdir(html_dir):
		json_filename = filename.replace('html','json')
		json_filepath = join(json_dir, json_filename)
		if os.path.exists(json_filepath):
			json_data_row = "<a href=\"json/{0}\">{0}</a>".format(json_filename)
		else:
			json_data_row = "No Tweets Captured"
		crawl_date_string = filename.split('-')[1].replace('.html','')
		crawl_date_object = datetime.datetime.strptime(crawl_date_string, "%Y%m%d%H%M%S")
		crawl_date = datetime.datetime.strftime(crawl_date_object, "%B %d, %Y")
		table_row = """
			<tr>
			<td>{0}</td>
			<td><a href="html/{1}">{1}</a></td>
			<td>{2}</td>
			</tr>
			""".format(crawl_date, filename, json_data_row)
		table_rows += table_row

	index_html = """ 
		<html>
		<head>
		<meta charset='utf-8'>
		<title>{0} Twitter Archive</title>
		<style type='text/css'>
		body {{
			font-family: Arial, Helvetica, sans-serif;
			font-size: 12px;
		}}
		h1, h2 {{
			text-align: center;
		}}
		table {{
			border: 0;
			border-collapse:collapse;
			margin: auto;
			border-spacing: 0;
		}}
		td, th {{
			margin: 0px;
			border: 1px solid #333;
			border-collapse:collapse;
			padding-top: 3px;
			padding-right: 8px;
			padding-bottom: 3px;
			padding-left: 8px;
		}}
		</style>
		</head>

		<body>
		<h1>Bentley Historical Library</h1>
		<h2>Archive of {1}</h2>
		<table>
		<thead>
			<tr>
				<th>Capture Date</th>
				<th>Tweet Wall</th>
				<th>Raw JSON Data</th>
			</tr>
		</thead>
		<tbody>
		{2}
		</tbody>
		</table>
		</body>
		</html>
		""".format(crawl_name, header_text, table_rows)

	with open(index,'w') as index_out:
		index_out.write(index_html)

def build_index(feeds):
	for feed in feeds:
		print "Building index.html for {0}".format(feed)
		feed_dict = feeds[feed]
		build_index_for_feed(feed_dict)