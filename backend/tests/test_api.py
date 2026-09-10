import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.main import app
from app.database import Base, get_db
from app.services.auth_service import seed_default_users

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

@pytest_asyncio.fixture
async def client():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    async with async_session() as session:
        await seed_default_users(session)

    async def override_get_db():
        async with async_session() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
        
    app.dependency_overrides.clear()
    await engine.dispose()

@pytest.mark.asyncio
async def test_auth_login(client):
    res = await client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["role"] == "ADMIN"

@pytest.mark.asyncio
async def test_simulation_create_and_status(client):
    create_payload = {
        "name": "Integration Test Sim",
        "num_banks": 3,
        "num_genuine_accounts": 30,
        "num_mule_accounts": 6,
        "num_compromised_accounts": 2,
        "min_starting_balance": 10000.0,
        "max_starting_balance": 50000.0,
        "distribution_type": "RANDOM",
        "scenario_type": "MULTI_HOP_MULE_NETWORK",
        "transaction_volume": "HIGH"
    }
    res = await client.post("/api/simulation/create", json=create_payload)
    assert res.status_code == 200
    data = res.json()
    assert data["total_banks"] == 3
    assert data["total_accounts"] == 38

    # Check Banks Endpoint
    res_banks = await client.get("/api/banks")
    assert res_banks.status_code == 200
    banks = res_banks.json()
    assert len(banks) == 3
    assert sum(b["total_accounts_count"] for b in banks) == 38

    # Check Accounts Endpoint
    res_accs = await client.get("/api/accounts")
    assert res_accs.status_code == 200
    accs = res_accs.json()
    assert len(accs) == 38
    assert "account_type_ground_truth" in accs[0]

    # Check Status Endpoint
    res_status = await client.get("/api/simulation/status")
    assert res_status.status_code == 200
    status_data = res_status.json()
    assert status_data["total_banks"] == 3
    assert status_data["total_accounts"] == 38
    assert status_data["genuine_accounts"] == 30
    assert status_data["mule_accounts"] == 6
    assert status_data["compromised_accounts"] == 2
