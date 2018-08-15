import unittest
import amaxa
from unittest.mock import Mock

class test_SalesforceId(unittest.TestCase):
    def test_converts_real_id_pairs(self):
        known_good_ids = {
            '01Q36000000RXX5': '01Q36000000RXX5EAO',
            '005360000016xkG': '005360000016xkGAAQ',
            '01I36000002zD9R': '01I36000002zD9REAU',
            '0013600001ohPTp': '0013600001ohPTpAAM',
            '0033600001gyv5B': '0033600001gyv5BAAQ'
        }

        for id_15 in known_good_ids:
            self.assertEqual(known_good_ids[id_15], str(amaxa.SalesforceId(id_15)))
            self.assertEqual(known_good_ids[id_15], amaxa.SalesforceId(id_15))

            self.assertEqual(id_15, amaxa.SalesforceId(id_15))
            self.assertNotEqual(id_15, str(amaxa.SalesforceId(id_15)))

            self.assertEqual(amaxa.SalesforceId(id_15), amaxa.SalesforceId(id_15))

            self.assertEqual(known_good_ids[id_15], amaxa.SalesforceId(known_good_ids[id_15]))
            self.assertEqual(known_good_ids[id_15], str(amaxa.SalesforceId(known_good_ids[id_15])))

            self.assertEqual(hash(known_good_ids[id_15]), hash(amaxa.SalesforceId(id_15)))
    
    def test_raises_valueerror(self):
        with self.assertRaises(ValueError):
            bad_id = amaxa.SalesforceId('test')
    
    def test_accepts_other_id(self):
        the_id = amaxa.SalesforceId('001000000000000')

        self.assertEqual(the_id, amaxa.SalesforceId(the_id))

class test_OperationContext(unittest.TestCase):
    def test_tracks_dependencies(self):
        connection = Mock()

        oc = amaxa.OperationContext(
            connection,
            ['Account']
        )

        self.assertEqual(set(), oc.get_dependencies('Account'))
        oc.add_dependency('Account', amaxa.SalesforceId('001000000000000'))
        self.assertEqual(set([amaxa.SalesforceId('001000000000000')]), oc.get_dependencies('Account'))

    def test_creates_and_caches_proxy_objects(self):
        connection = Mock()
        connection.SFType = Mock(return_value='Account')

        oc = amaxa.OperationContext(
            connection,
            ['Account']
        )

        proxy = oc.get_proxy_object('Account')

        self.assertEqual('Account', proxy)
        connection.SFType.assert_called_once_with('Account')

        connection.reset_mock()
        proxy = oc.get_proxy_object('Account')

        # Proxy should be cached
        self.assertEqual('Account', proxy)
        connection.SFType.assert_not_called()
    
    def test_caches_describe_results(self):
        connection = Mock()
        account_mock = Mock()

        fields = [{ 'name': 'Name' }, { 'name': 'Id' }]
        describe_info = { 'fields' : fields }
        account_mock.describe = Mock(return_value=describe_info)
        connection.SFType = Mock(return_value=account_mock)

        oc = amaxa.OperationContext(
            connection,
            ['Account']
        )

        retval = oc.get_describe('Account')
        self.assertEqual(describe_info, retval)
        account_mock.describe.assert_called_once_with()
        account_mock.describe.reset_mock()

        retval = oc.get_describe('Account')
        self.assertEqual(describe_info, retval)
        account_mock.describe.assert_not_called()
    
    def test_caches_field_maps(self):
        connection = Mock()
        account_mock = Mock()

        fields = [{ 'name': 'Name' }, { 'name': 'Id' }]
        describe_info = { 'fields' : fields }
        account_mock.describe = Mock(return_value=describe_info)
        connection.SFType = Mock(return_value=account_mock)

        oc = amaxa.OperationContext(
            connection,
            ['Account']
        )

        retval = oc.get_field_map('Account')
        self.assertEqual({ 'Name': { 'name': 'Name' }, 'Id': { 'name': 'Id' } }, retval)
        account_mock.describe.assert_called_once_with()
        account_mock.describe.reset_mock()

        retval = oc.get_field_map('Account')
        self.assertEqual({ 'Name': { 'name': 'Name' }, 'Id': { 'name': 'Id' } }, retval)
        account_mock.describe.assert_not_called()
    
    def test_filters_field_maps(self):
        connection = Mock()
        account_mock = Mock()

        fields = [{ 'name': 'Name' }, { 'name': 'Id' }]
        describe_info = { 'fields' : fields }
        account_mock.describe = Mock(return_value=describe_info)
        connection.SFType = Mock(return_value=account_mock)

        oc = amaxa.OperationContext(
            connection,
            ['Account']
        )

        retval = oc.get_filtered_field_map('Account', lambda f: f['name'] == 'Id')
        self.assertEqual({ 'Id': { 'name': 'Id' } }, retval)

    def test_store_result_retains_ids(self):
        connection = Mock()

        oc = amaxa.OperationContext(
            connection,
            ['Account']
        )

        oc.output_files['Account'] = Mock()

        oc.store_result('Account', { 'Id': '001000000000000', 'Name': 'Caprica Steel' })
        self.assertEqual(set([amaxa.SalesforceId('001000000000000')]), oc.extracted_ids['Account'])

    def test_store_result_writes_records(self):
        connection = Mock()

        oc = amaxa.OperationContext(
            connection,
            ['Account']
        )

        account_mock = Mock()
        oc.output_files['Account'] = account_mock

        oc.store_result('Account', { 'Id': '001000000000000', 'Name': 'Caprica Steel' })
        account_mock.writerow.assert_called_once_with({ 'Id': '001000000000000', 'Name': 'Caprica Steel' })
    
    def test_store_result_transforms_output(self):
        connection = Mock()

        oc = amaxa.OperationContext(
            connection,
            ['Account']
        )

        account_mock = Mock()
        oc.output_files['Account'] = account_mock
        mapper_mock = Mock()
        mapper_mock.transform_record = Mock(return_value = { 'Id': '001000000000000', 'Name': 'Caprica City Steel' })

        oc.mappers['Account'] = mapper_mock

        oc.store_result('Account', { 'Id': '001000000000000', 'Name': 'Caprica Steel' })
        mapper_mock.transform_record.assert_called_once_with({ 'Id': '001000000000000', 'Name': 'Caprica Steel' })
        account_mock.writerow.assert_called_once_with({ 'Id': '001000000000000', 'Name': 'Caprica City Steel' })
    
    def test_store_result_clears_dependencies(self):
        connection = Mock()

        oc = amaxa.OperationContext(
            connection,
            ['Account']
        )

        oc.output_files['Account'] = Mock()
        oc.add_dependency('Account', '001000000000000')

        oc.store_result('Account', { 'Id': '001000000000000', 'Name': 'Caprica Steel' })
        self.assertEqual(set(), oc.get_dependencies('Account'))

    def test_get_extracted_ids_returns_results(self):
        connection = Mock()

        oc = amaxa.OperationContext(
            connection,
            ['Account']
        )

        oc.output_files['Account'] = Mock()

        oc.store_result('Account', { 'Id': '001000000000000', 'Name': 'Caprica Steel' })
        self.assertEqual(set([amaxa.SalesforceId('001000000000000')]), oc.get_extracted_ids('Account'))

    def test_get_sobject_ids_for_reference_returns_correct_ids(self):
        connection = Mock()

        oc = amaxa.OperationContext(
            connection,
            ['Account', 'Contact', 'Opportunity']
        )

        oc.output_files['Account'] = Mock()
        oc.output_files['Contact'] = Mock()
        oc.output_files['Opportunity'] = Mock()
        oc.get_field_map = Mock(return_value={ 'Lookup__c': { 'referenceTo': ['Account', 'Contact'] }})

        oc.store_result('Account', { 'Id': '001000000000000', 'Name': 'University of Caprica' })
        oc.store_result('Contact', { 'Id': '003000000000000', 'Name': 'Gaius Baltar' })
        oc.store_result('Opportunity', { 'Id': '006000000000000', 'Name': 'Defense Mainframe' })

        self.assertEqual(set([amaxa.SalesforceId('001000000000000'), amaxa.SalesforceId('003000000000000')]),
                         oc.get_sobject_ids_for_reference('Account', 'Lookup__c'))


class test_ExtractMapper(unittest.TestCase):
    def test_transform_key_applies_mapping(self):
        pass
    
    def test_transform_value_applies_transformations(self):
        pass
    
    def test_transform_record_does(self):
        pass

class test_SingleObjectExtraction(unittest.TestCase):
    def test_identifies_self_lookups(self):
        connection = Mock()

        oc = amaxa.OperationContext(
            connection,
            ['Account', 'Contact', 'Opportunity']
        )

        oc.output_files['Account'] = Mock()
        oc.output_files['Contact'] = Mock()
        oc.output_files['Opportunity'] = Mock()
        oc.get_field_map = Mock(return_value={ 
            'Lookup__c': { 
                'name': 'Lookup__c',
                'type': 'reference',
                'referenceTo': ['Account']
            }, 
            'Other__c': { 
                'name': 'Other__c',
                'type': 'reference',
                'referenceTo': ['Contact'] 
            }
        })

        step = amaxa.SingleObjectExtraction('Account', amaxa.ExtractionScope.ALL_RECORDS, ['Lookup__c', 'Other__c'], oc)

        self.assertEqual(set(['Lookup__c']), step.self_lookups)


    def test_throws_exception_for_polymorphic_self_lookup(self):
        connection = Mock()

        oc = amaxa.OperationContext(
            connection,
            ['Account', 'Contact', 'Opportunity']
        )

        oc.output_files['Account'] = Mock()
        oc.output_files['Contact'] = Mock()
        oc.output_files['Opportunity'] = Mock()
        oc.get_field_map = Mock(return_value={ 
            'Lookup__c': { 
                'name': 'Lookup__c',
                'type': 'reference',
                'referenceTo': ['Account', 'Contact']
            }, 
            'Other__c': { 
                'name': 'Other__c',
                'type': 'reference',
                'referenceTo': ['Contact'] 
            }
        })

        with self.assertRaises(AssertionError):
            step = amaxa.SingleObjectExtraction('Account', amaxa.ExtractionScope.ALL_RECORDS, ['Lookup__c', 'Other__c'], oc)

    def test_generates_field_list(self):
        connection = Mock()

        oc = amaxa.OperationContext(
            connection,
            ['Account', 'Contact', 'Opportunity']
        )

        oc.output_files['Account'] = Mock()
        oc.output_files['Contact'] = Mock()
        oc.output_files['Opportunity'] = Mock()
        oc.get_field_map = Mock(return_value={ 
            'Lookup__c': { 
                'name': 'Lookup__c',
                'type': 'reference',
                'referenceTo': ['Account']
            }, 
            'Other__c': { 
                'name': 'Other__c',
                'type': 'reference',
                'referenceTo': ['Contact'] 
            }
        })

        step = amaxa.SingleObjectExtraction('Account', amaxa.ExtractionScope.ALL_RECORDS, ['Lookup__c', 'Other__c'], oc)

        self.assertEqual('Lookup__c, Other__c', step.get_field_list())

    def test_store_result_calls_context(self):
        connection = Mock()

        oc = amaxa.OperationContext(
            connection,
            ['Account']
        )

        oc.store_result = Mock()
        oc.add_dependency = Mock()
        oc.get_field_map = Mock(return_value={ 
            'Lookup__c': { 
                'name': 'Lookup__c',
                'type': 'reference',
                'referenceTo': ['Account']
            }
        })

        step = amaxa.SingleObjectExtraction('Account', amaxa.ExtractionScope.ALL_RECORDS, [], oc)

        step.store_result({ 'Id': '001000000000000', 'Name': 'Picon Fleet Headquarters' })
        oc.store_result.assert_called_once_with('Account', { 'Id': '001000000000000', 'Name': 'Picon Fleet Headquarters' })
        oc.add_dependency.assert_not_called()

    def test_store_result_registers_self_lookup_dependencies(self):
        connection = Mock()

        oc = amaxa.OperationContext(
            connection,
            ['Account']
        )

        oc.store_result = Mock()
        oc.add_dependency = Mock()
        oc.get_field_map = Mock(return_value={ 
            'Lookup__c': { 
                'name': 'Lookup__c',
                'type': 'reference',
                'referenceTo': ['Account']
            }
        })

        step = amaxa.SingleObjectExtraction('Account', amaxa.ExtractionScope.ALL_RECORDS, ['Lookup__c'], oc)

        step.store_result({ 'Id': '001000000000000', 'Lookup__c': '001000000000001', 'Name': 'Picon Fleet Headquarters' })
        oc.add_dependency.assert_called_once_with('Account', '001000000000001')

    def test_perform_lookup_pass_executes_correct_query(self):
        connection = Mock()

        oc = amaxa.OperationContext(
            connection,
            ['Account']
        )

        oc.get_field_map = Mock(return_value={ 
            'Lookup__c': { 
                'name': 'Lookup__c',
                'type': 'reference',
                'referenceTo': ['Account']
            }
        })
        oc.get_sobject_ids_for_reference = Mock(return_value=set([amaxa.SalesforceId('001000000000000')]))

        step = amaxa.SingleObjectExtraction('Account', amaxa.ExtractionScope.ALL_RECORDS, ['Lookup__c'], oc)

        step.perform_id_field_pass = Mock()
        step.perform_lookup_pass('Lookup__c')

        oc.get_sobject_ids_for_reference.assert_called_once_with('Account', 'Lookup__c')
        step.perform_id_field_pass.assert_called_once_with('Lookup__c', set([amaxa.SalesforceId('001000000000000')]))

    def test_perform_id_field_pass_queries_all_records(self):
        pass
    
    def test_perform_bulk_api_pass_extracts_records(self):
        pass
    
    def test_resolve_registered_dependencies_loads_records(self):
        pass
    
    def test_resolve_registered_dependencies_throws_exception_for_missing_ids(self):
        pass
    
    def test_execute_with_all_records_performs_bulk_api_pass(self):
        pass
    
    def test_execute_with_query_performs_bulk_api_pass(self):
        pass

    def test_execute_loads_all_descendents(self):
        pass

    def test_execute_resolves_self_lookups(self):
        pass

    def test_execute_resolves_dependencies(self):
        pass


if __name__ == "__main__":
    unittest.main()