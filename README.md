valuenetwork
=====================

A prototype of Value Network Accounting, being developed in collaboration with http://www.sensorica.co/ , a pioneering value network.

Background on Value Networks: http://www.sensorica.co/value-networks

The prototype used the https://github.com/pinax/pinax-project-account starter project, built on the Django framework.

Developer doc to come.  User doc probably much later.

The valueaccounting app could be split out and used in other Django projects.

Roadmap:

* Deploy on Web server so Sensorica members can experiment with it.
* Import Sensorica spreadsheet data.
* Create interfaces for members to enter contributions.
* Create an interface for members to experiment with value equations and income distributions.
* Create a pluggable English vocabulary.
* Translate the UI into French.
* Create visualizations in the system.
* Create exports of combined data for visualizations and reports outside the system.
* Add a reversion system (version tracking and undo) for data changes.

Longer term:
* Create a protocol for nodes in a federated value system to communicate and transact with one another.
* Convert the valueaccounting Django app to another platform to test the protocol between platforms and serve as a proof of concept of a language and framework neutral accounting design..

