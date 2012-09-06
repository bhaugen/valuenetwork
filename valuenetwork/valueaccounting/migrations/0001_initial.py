# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'ValueEquation'
        db.create_table('valueaccounting_valueequation', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('base_rate', self.gf('django.db.models.fields.DecimalField')(max_digits=8, decimal_places=2)),
            ('role_weight', self.gf('django.db.models.fields.DecimalField')(max_digits=6, decimal_places=4)),
            ('importance_weight', self.gf('django.db.models.fields.DecimalField')(max_digits=6, decimal_places=4)),
            ('quality_weight', self.gf('django.db.models.fields.DecimalField')(max_digits=6, decimal_places=4)),
            ('accountability_weight', self.gf('django.db.models.fields.DecimalField')(max_digits=6, decimal_places=4)),
            ('regularity_weight', self.gf('django.db.models.fields.DecimalField')(max_digits=6, decimal_places=4)),
            ('reputation_weight', self.gf('django.db.models.fields.DecimalField')(max_digits=6, decimal_places=4)),
            ('risk_weight', self.gf('django.db.models.fields.DecimalField')(max_digits=6, decimal_places=4)),
            ('commitment_weight', self.gf('django.db.models.fields.DecimalField')(max_digits=6, decimal_places=4)),
            ('seniority_weight', self.gf('django.db.models.fields.DecimalField')(max_digits=6, decimal_places=4)),
        ))
        db.send_create_signal('valueaccounting', ['ValueEquation'])

        # Adding model 'Unit'
        db.create_table('valueaccounting_unit', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('unit_type', self.gf('django.db.models.fields.CharField')(max_length=12)),
            ('abbrev', self.gf('django.db.models.fields.CharField')(max_length=8)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=64)),
            ('symbol', self.gf('django.db.models.fields.CharField')(max_length=1, blank=True)),
        ))
        db.send_create_signal('valueaccounting', ['Unit'])

        # Adding model 'AgentType'
        db.create_table('valueaccounting_agenttype', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=128)),
        ))
        db.send_create_signal('valueaccounting', ['AgentType'])

        # Adding model 'EconomicAgent'
        db.create_table('valueaccounting_economicagent', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('agent_type', self.gf('django.db.models.fields.related.ForeignKey')(related_name='agents', to=orm['valueaccounting.AgentType'])),
            ('description', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('address', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('latitude', self.gf('django.db.models.fields.FloatField')(default=0.0, null=True, blank=True)),
            ('longitude', self.gf('django.db.models.fields.FloatField')(default=0.0, null=True, blank=True)),
            ('slug', self.gf('django.db.models.fields.SlugField')(max_length=50)),
        ))
        db.send_create_signal('valueaccounting', ['EconomicAgent'])

        # Adding model 'EconomicResourceType'
        db.create_table('valueaccounting_economicresourcetype', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('parent', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='children', null=True, to=orm['valueaccounting.EconomicResourceType'])),
            ('slug', self.gf('django.db.models.fields.SlugField')(max_length=50)),
            ('unit', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='resource_units', null=True, to=orm['valueaccounting.Unit'])),
        ))
        db.send_create_signal('valueaccounting', ['EconomicResourceType'])

        # Adding model 'EconomicResource'
        db.create_table('valueaccounting_economicresource', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('resource_type', self.gf('django.db.models.fields.related.ForeignKey')(related_name='resources', to=orm['valueaccounting.EconomicResourceType'])),
            ('identifier', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('owner', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='owned_resources', null=True, to=orm['valueaccounting.EconomicAgent'])),
            ('custodian', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='custody_resources', null=True, to=orm['valueaccounting.EconomicAgent'])),
            ('created_date', self.gf('django.db.models.fields.DateField')()),
        ))
        db.send_create_signal('valueaccounting', ['EconomicResource'])

        # Adding model 'ProcessType'
        db.create_table('valueaccounting_processtype', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('slug', self.gf('django.db.models.fields.SlugField')(max_length=50)),
        ))
        db.send_create_signal('valueaccounting', ['ProcessType'])

        # Adding model 'Process'
        db.create_table('valueaccounting_process', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('process_type', self.gf('django.db.models.fields.related.ForeignKey')(related_name='processes', to=orm['valueaccounting.ProcessType'])),
            ('start_date', self.gf('django.db.models.fields.DateField')()),
            ('end_date', self.gf('django.db.models.fields.DateField')(null=True, blank=True)),
            ('managed_by', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='managed_processes', null=True, to=orm['valueaccounting.EconomicAgent'])),
            ('owner', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='owned_processes', null=True, to=orm['valueaccounting.EconomicAgent'])),
            ('notes', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('slug', self.gf('django.db.models.fields.SlugField')(max_length=50)),
        ))
        db.send_create_signal('valueaccounting', ['Process'])

        # Adding model 'EventType'
        db.create_table('valueaccounting_eventtype', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('resource_effect', self.gf('django.db.models.fields.CharField')(max_length=12)),
            ('unit_type', self.gf('django.db.models.fields.CharField')(max_length=12)),
            ('slug', self.gf('django.db.models.fields.SlugField')(max_length=50)),
        ))
        db.send_create_signal('valueaccounting', ['EventType'])

        # Adding model 'Role'
        db.create_table('valueaccounting_role', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('factor', self.gf('django.db.models.fields.DecimalField')(max_digits=6, decimal_places=4)),
            ('slug', self.gf('django.db.models.fields.SlugField')(max_length=50)),
        ))
        db.send_create_signal('valueaccounting', ['Role'])

        # Adding model 'EconomicEvent'
        db.create_table('valueaccounting_economicevent', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('event_type', self.gf('django.db.models.fields.related.ForeignKey')(related_name='events', to=orm['valueaccounting.EventType'])),
            ('event_date', self.gf('django.db.models.fields.DateField')()),
            ('from_agent', self.gf('django.db.models.fields.related.ForeignKey')(related_name='given_events', to=orm['valueaccounting.EconomicAgent'])),
            ('from_agent_role', self.gf('django.db.models.fields.related.ForeignKey')(related_name='events', to=orm['valueaccounting.Role'])),
            ('to_agent', self.gf('django.db.models.fields.related.ForeignKey')(related_name='taken_events', to=orm['valueaccounting.EconomicAgent'])),
            ('resource_type', self.gf('django.db.models.fields.related.ForeignKey')(related_name='events', to=orm['valueaccounting.EconomicResourceType'])),
            ('resource', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='events', null=True, to=orm['valueaccounting.EconomicResource'])),
            ('process', self.gf('django.db.models.fields.related.ForeignKey')(related_name='events', to=orm['valueaccounting.Process'])),
            ('amount', self.gf('django.db.models.fields.DecimalField')(max_digits=8, decimal_places=2)),
            ('unit', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='event_units', null=True, to=orm['valueaccounting.Unit'])),
            ('notes', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('created_by', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='events_created', null=True, to=orm['auth.User'])),
            ('changed_by', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='events_changed', null=True, to=orm['auth.User'])),
            ('slug', self.gf('django.db.models.fields.SlugField')(max_length=50)),
        ))
        db.send_create_signal('valueaccounting', ['EconomicEvent'])


    def backwards(self, orm):
        # Deleting model 'ValueEquation'
        db.delete_table('valueaccounting_valueequation')

        # Deleting model 'Unit'
        db.delete_table('valueaccounting_unit')

        # Deleting model 'AgentType'
        db.delete_table('valueaccounting_agenttype')

        # Deleting model 'EconomicAgent'
        db.delete_table('valueaccounting_economicagent')

        # Deleting model 'EconomicResourceType'
        db.delete_table('valueaccounting_economicresourcetype')

        # Deleting model 'EconomicResource'
        db.delete_table('valueaccounting_economicresource')

        # Deleting model 'ProcessType'
        db.delete_table('valueaccounting_processtype')

        # Deleting model 'Process'
        db.delete_table('valueaccounting_process')

        # Deleting model 'EventType'
        db.delete_table('valueaccounting_eventtype')

        # Deleting model 'Role'
        db.delete_table('valueaccounting_role')

        # Deleting model 'EconomicEvent'
        db.delete_table('valueaccounting_economicevent')


    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'valueaccounting.agenttype': {
            'Meta': {'ordering': "('name',)", 'object_name': 'AgentType'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128'})
        },
        'valueaccounting.economicagent': {
            'Meta': {'ordering': "('name',)", 'object_name': 'EconomicAgent'},
            'address': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'agent_type': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'agents'", 'to': "orm['valueaccounting.AgentType']"}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'latitude': ('django.db.models.fields.FloatField', [], {'default': '0.0', 'null': 'True', 'blank': 'True'}),
            'longitude': ('django.db.models.fields.FloatField', [], {'default': '0.0', 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '50'})
        },
        'valueaccounting.economicevent': {
            'Meta': {'ordering': "('event_date',)", 'object_name': 'EconomicEvent'},
            'amount': ('django.db.models.fields.DecimalField', [], {'max_digits': '8', 'decimal_places': '2'}),
            'changed_by': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'events_changed'", 'null': 'True', 'to': "orm['auth.User']"}),
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'events_created'", 'null': 'True', 'to': "orm['auth.User']"}),
            'event_date': ('django.db.models.fields.DateField', [], {}),
            'event_type': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'events'", 'to': "orm['valueaccounting.EventType']"}),
            'from_agent': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'given_events'", 'to': "orm['valueaccounting.EconomicAgent']"}),
            'from_agent_role': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'events'", 'to': "orm['valueaccounting.Role']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'notes': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'process': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'events'", 'to': "orm['valueaccounting.Process']"}),
            'resource': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'events'", 'null': 'True', 'to': "orm['valueaccounting.EconomicResource']"}),
            'resource_type': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'events'", 'to': "orm['valueaccounting.EconomicResourceType']"}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '50'}),
            'to_agent': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'taken_events'", 'to': "orm['valueaccounting.EconomicAgent']"}),
            'unit': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'event_units'", 'null': 'True', 'to': "orm['valueaccounting.Unit']"})
        },
        'valueaccounting.economicresource': {
            'Meta': {'ordering': "('resource_type', 'identifier')", 'object_name': 'EconomicResource'},
            'created_date': ('django.db.models.fields.DateField', [], {}),
            'custodian': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'custody_resources'", 'null': 'True', 'to': "orm['valueaccounting.EconomicAgent']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'identifier': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'owned_resources'", 'null': 'True', 'to': "orm['valueaccounting.EconomicAgent']"}),
            'resource_type': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'resources'", 'to': "orm['valueaccounting.EconomicResourceType']"})
        },
        'valueaccounting.economicresourcetype': {
            'Meta': {'ordering': "('name',)", 'object_name': 'EconomicResourceType'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'children'", 'null': 'True', 'to': "orm['valueaccounting.EconomicResourceType']"}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '50'}),
            'unit': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'resource_units'", 'null': 'True', 'to': "orm['valueaccounting.Unit']"})
        },
        'valueaccounting.eventtype': {
            'Meta': {'ordering': "('name',)", 'object_name': 'EventType'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'resource_effect': ('django.db.models.fields.CharField', [], {'max_length': '12'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '50'}),
            'unit_type': ('django.db.models.fields.CharField', [], {'max_length': '12'})
        },
        'valueaccounting.process': {
            'Meta': {'ordering': "('name',)", 'object_name': 'Process'},
            'end_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'managed_by': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'managed_processes'", 'null': 'True', 'to': "orm['valueaccounting.EconomicAgent']"}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'notes': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'owned_processes'", 'null': 'True', 'to': "orm['valueaccounting.EconomicAgent']"}),
            'process_type': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'processes'", 'to': "orm['valueaccounting.ProcessType']"}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '50'}),
            'start_date': ('django.db.models.fields.DateField', [], {})
        },
        'valueaccounting.processtype': {
            'Meta': {'ordering': "('name',)", 'object_name': 'ProcessType'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '50'})
        },
        'valueaccounting.role': {
            'Meta': {'ordering': "('name',)", 'object_name': 'Role'},
            'factor': ('django.db.models.fields.DecimalField', [], {'max_digits': '6', 'decimal_places': '4'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '50'})
        },
        'valueaccounting.unit': {
            'Meta': {'ordering': "('abbrev',)", 'object_name': 'Unit'},
            'abbrev': ('django.db.models.fields.CharField', [], {'max_length': '8'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'symbol': ('django.db.models.fields.CharField', [], {'max_length': '1', 'blank': 'True'}),
            'unit_type': ('django.db.models.fields.CharField', [], {'max_length': '12'})
        },
        'valueaccounting.valueequation': {
            'Meta': {'object_name': 'ValueEquation'},
            'accountability_weight': ('django.db.models.fields.DecimalField', [], {'max_digits': '6', 'decimal_places': '4'}),
            'base_rate': ('django.db.models.fields.DecimalField', [], {'max_digits': '8', 'decimal_places': '2'}),
            'commitment_weight': ('django.db.models.fields.DecimalField', [], {'max_digits': '6', 'decimal_places': '4'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'importance_weight': ('django.db.models.fields.DecimalField', [], {'max_digits': '6', 'decimal_places': '4'}),
            'quality_weight': ('django.db.models.fields.DecimalField', [], {'max_digits': '6', 'decimal_places': '4'}),
            'regularity_weight': ('django.db.models.fields.DecimalField', [], {'max_digits': '6', 'decimal_places': '4'}),
            'reputation_weight': ('django.db.models.fields.DecimalField', [], {'max_digits': '6', 'decimal_places': '4'}),
            'risk_weight': ('django.db.models.fields.DecimalField', [], {'max_digits': '6', 'decimal_places': '4'}),
            'role_weight': ('django.db.models.fields.DecimalField', [], {'max_digits': '6', 'decimal_places': '4'}),
            'seniority_weight': ('django.db.models.fields.DecimalField', [], {'max_digits': '6', 'decimal_places': '4'})
        }
    }

    complete_apps = ['valueaccounting']