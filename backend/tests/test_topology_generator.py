import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.future import select
from app.database import Base
from app.models.account import Account, GroundTruthAccountType
from app.schemas.simulation import SimulationConfigCreate, CustomBankAllocation, DistributionType, TransactionVolume
from app.services.topology_generator import generate_simulation_topology

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

@pytest_asyncio.fixture
async def test_db():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    async with async_session() as session:
        yield session
        
    await engine.dispose()

@pytest.mark.asyncio
async def test_random_topology_generation(test_db):
    config = SimulationConfigCreate(
        name="Test Random Scenario",
        num_banks=5,
        num_genuine_accounts=50,
        num_mule_accounts=10,
        num_compromised_accounts=5,
        min_starting_balance=10000.0,
        max_starting_balance=100000.0,
        distribution_type=DistributionType.RANDOM,
        scenario_type="MULTI_HOP_MULE_NETWORK",
        transaction_volume=TransactionVolume.HIGH
    )
    
    sim_config, banks, accounts = await generate_simulation_topology(config, test_db)
    
    assert len(banks) == 5
    assert len(accounts) == 65
    
    genuine_accs = [a for a in accounts if a.account_type_ground_truth == GroundTruthAccountType.GENUINE.value]
    mule_accs = [a for a in accounts if a.account_type_ground_truth == GroundTruthAccountType.MULE.value]
    comp_accs = [a for a in accounts if a.account_type_ground_truth == GroundTruthAccountType.COMPROMISED.value]
    
    assert len(genuine_accs) == 50
    assert len(mule_accs) == 10
    assert len(comp_accs) == 5
    
    # Query from test_db to verify persistence
    from sqlalchemy.orm import selectinload
    res = await test_db.execute(select(Account).options(selectinload(Account.profile)))
    persisted_accs = res.scalars().all()
    assert len(persisted_accs) == 65
    for a in persisted_accs:
        assert 10000.0 <= a.ledger_balance <= 100000.0
        assert a.available_balance == a.ledger_balance
        assert a.profile is not None

@pytest.mark.asyncio
async def test_custom_topology_generation(test_db):
    custom_alloc = [
        CustomBankAllocation(bank_name="Alpha Bank", bank_code="ALPH", genuine_count=20, mule_count=5, compromised_count=2),
        CustomBankAllocation(bank_name="Beta Bank", bank_code="BETA", genuine_count=30, mule_count=3, compromised_count=1),
    ]
    config = SimulationConfigCreate(
        name="Test Custom Scenario",
        num_banks=2,
        num_genuine_accounts=50,
        num_mule_accounts=8,
        num_compromised_accounts=3,
        min_starting_balance=20000.0,
        max_starting_balance=50000.0,
        distribution_type=DistributionType.CUSTOM,
        custom_distribution=custom_alloc,
        scenario_type="CROSS_BANK_MULE_NETWORK"
    )
    
    sim_config, banks, accounts = await generate_simulation_topology(config, test_db)
    
    assert len(banks) == 2
    assert banks[0].bank_name == "Alpha Bank"
    assert banks[1].bank_name == "Beta Bank"
    assert len(accounts) == 61
