import unittest
from unittest.mock import patch
import nasa_hub as hub
from media_catalog import BY_ID, COLLECTIONS
from web_server import app


class MediaTests(unittest.TestCase):
    def test_all_eight_planets_and_moon_are_available(self):
        self.assertTrue({'mercury','venus','earth','mars','jupiter','saturn','uranus','neptune','moon'} <= BY_ID.keys())
        self.assertEqual(len(BY_ID), len(COLLECTIONS))

    def test_preset_filters_and_pagination(self):
        raw = {'collection':{'items':[{'data':[{'nasa_id':'PIA123','title':'Venus','secondary_creator':'NASA/JPL','date_created':'2020-01-01','description':'Radar image'}],'links':[{'render':'image','href':'https://images-assets.nasa.gov/venus.jpg'}]}],'metadata':{'total_hits':60}}}
        with patch.object(hub,'get_json',return_value=raw) as get:
            result=hub.media('ignored',2,'venus')
            params=get.call_args.args[1]
            self.assertEqual(params['page'],2)
            self.assertEqual(params['center'],'JPL')
            self.assertEqual(params['title'],'Venus')
            self.assertEqual(result['pages'],3)
            self.assertEqual(result['items'][0]['credit'],'NASA/JPL')

    def test_media_types_do_not_call_illustrations_photos(self):
        self.assertEqual(hub.media_kind('Exoplanet',"Artist's impression of a planet"),'illustration')
        self.assertEqual(hub.media_kind('Planet spectrum',''),'diagram')
        self.assertEqual(hub.media_kind('Webb mirror deployment',''),'hardware')
        self.assertEqual(hub.media_kind('Nebula','A composite from infrared observations'),'image')

    def test_asset_selects_original_and_rejects_unsafe_links(self):
        raw={'collection':{'items':[{'href':'https://images-assets.nasa.gov/a~small.jpg'},{'href':'javascript:alert(1)'},{'href':'http://images-assets.nasa.gov/a~orig.jpg'},{'href':'https://images-assets.nasa.gov/metadata.json'}]}}
        with patch.object(hub,'get_json',return_value=raw):
            self.assertEqual(hub.asset('PIA123')['original_url'],'https://images-assets.nasa.gov/a~orig.jpg')

    def test_routes_validate_and_dispatch_collection(self):
        with app.test_client() as client, patch.object(hub,'snapshot',return_value={'status':'loading','data':None}) as snap:
            for path in ['/api/explore/media?page=0','/api/explore/media?page=101','/api/explore/media?page=x','/api/explore/media?collection=unknown','/api/explore/asset?id=../foo']:
                self.assertEqual(client.get(path).status_code,400)
            self.assertEqual(client.get('/api/explore/media?collection=neptune&page=2').status_code,200)
            snap.assert_called_with('media',BY_ID['neptune']['query'],2,'neptune')
            catalog=client.get('/api/media/collections').json
            self.assertEqual(len(catalog['collections']),24)
            self.assertEqual(len(catalog['groups']),4)

if __name__=='__main__':unittest.main()
