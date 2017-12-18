# Groove Extractor
This script extracts all tickets, ticket states, and messages from your [Groove](https://www.groovehq.com) account. It creates a simple sqlite database.

## Motivation

According to the [Groove Knowledge Base](https://help.groovehq.com/knowledge_base/topics/how-do-i-export-my-contacts-tickets-reports):

> How do I export my contacts, tickets, reports?
>
> There's no automatic way to export any of your data at the moment. 
>
> Status: Planned
>
> ETA: Unknown
>
> As a workaround in the meantime, you can manually export your ticket and contact data using our API. We do not currently have an API for reports.

## Usage

This script was tested on 3.6. It does not require any external dependencies.

You need an API token. You an easily grab that by going to "Settings", "API", and grabbing the value in the "Private Token" field. Then just run:

> python extractor.py yourtokenhere

The process will be rather slow due to Groove's API design. We need to issue a request for every single ticket to find out its state.