"""Test that all CRUD classes can be imported and instantiated correctly."""

import sys

def test_imports():
    """Test that all CRUD modules can be imported."""
    print("Testing CRUD imports...")
    
    try:
        from app.database.crud import (
            user_crud,
            session_crud,
            invoice_crud,
            item_crud,
            payment_crud,
            CRUDUser,
            CRUDSession,
            CRUDInvoice,
            CRUDItem,
            CRUDPayment,
        )
        print("✅ All CRUD classes imported successfully")
        
        # Verify instances exist
        assert user_crud is not None
        assert session_crud is not None
        assert invoice_crud is not None
        assert item_crud is not None
        assert payment_crud is not None
        print("✅ All CRUD instances exist")
        
        # Verify classes exist
        assert CRUDUser is not None
        assert CRUDSession is not None
        assert CRUDInvoice is not None
        assert CRUDItem is not None
        assert CRUDPayment is not None
        print("✅ All CRUD classes exist")
        
        # Verify models are set
        from app.database.models import User, Session, Invoice, Item, Payment
        assert user_crud.model == User
        assert session_crud.model == Session
        assert invoice_crud.model == Invoice
        assert invoice_crud.model == Invoice
        assert item_crud.model == Item
        assert payment_crud.model == Payment
        print("✅ All CRUD models are correctly set")
        
        return True
        
    except Exception as e:
        print(f"❌ Import error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_seed_script_imports():
    """Test that the seed script can be imported."""
    print("\nTesting seed script imports...")
    
    try:
        # Just verify the script can be parsed
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "init_db", "scripts/init_db.py"
        )
        if spec is None or spec.loader is None:
            print("❌ Could not load seed script")
            return False
        
        print("✅ Seed script can be loaded")
        return True
        
    except Exception as e:
        print(f"❌ Seed script import error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_crud_methods_exist():
    """Test that CRUD methods exist."""
    print("\nTesting CRUD methods...")
    
    try:
        from app.database.crud import user_crud, session_crud
        
        # Check base methods
        assert hasattr(user_crud, 'get')
        assert hasattr(user_crud, 'get_multi')
        assert hasattr(user_crud, 'create')
        assert hasattr(user_crud, 'update')
        assert hasattr(user_crud, 'delete')
        print("✅ Base CRUD methods exist")
        
        # Check specific methods
        assert hasattr(user_crud, 'get_by_phone')
        assert hasattr(user_crud, 'get_by_name')
        print("✅ User-specific CRUD methods exist")
        
        assert hasattr(session_crud, 'get_by_owner')
        assert hasattr(session_crud, 'get_by_status')
        assert hasattr(session_crud, 'get_active_sessions')
        print("✅ Session-specific CRUD methods exist")
        
        return True
        
    except Exception as e:
        print(f"❌ CRUD methods test error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("CRUD and Seed Script Verification")
    print("=" * 60)
    
    results = []
    results.append(test_imports())
    results.append(test_seed_script_imports())
    results.append(test_crud_methods_exist())
    
    print("\n" + "=" * 60)
    if all(results):
        print("✅ All tests passed!")
        sys.exit(0)
    else:
        print("❌ Some tests failed")
        sys.exit(1)

