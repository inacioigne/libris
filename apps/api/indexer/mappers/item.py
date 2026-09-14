from indexer.documents.item import ItemSearchDocument
from models.item import Item


class ItemMapper:

    @staticmethod
    def to_search_document(item: Item) -> ItemSearchDocument:
        return ItemSearchDocument(
            id=item.id,
            instance_id=item.instance_id,
            uri=item.uri,
            barcode=item.barcode,
            location=item.location,
            call_number=item.call_number,
            status=item.status,
        )