#include "EnterpriseCV6Actor.h"
#include "Components/SceneComponent.h"
#include "Components/StaticMeshComponent.h"
#include "UObject/ConstructorHelpers.h"
#include "WarSimStateBridge.h"

AEnterpriseCV6Actor::AEnterpriseCV6Actor()
{
    PrimaryActorTick.bCanEverTick = true;
    ShipRoot = CreateDefaultSubobject<USceneComponent>(TEXT("ShipRoot"));
    SetRootComponent(ShipRoot);

    CompatibilityExterior = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("CompatibilityExterior"));
    CompatibilityExterior->SetupAttachment(ShipRoot);
    CompatibilityExterior->SetMobility(EComponentMobility::Movable);

    HullDeckHangar = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("HullDeckHangar"));
    HullDeckHangar->SetupAttachment(ShipRoot);
    IslandExterior = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("IslandExterior"));
    IslandExterior->SetupAttachment(ShipRoot);
    WeaponsFittings = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("WeaponsFittings"));
    WeaponsFittings->SetupAttachment(ShipRoot);
    DeckAircraft = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("DeckAircraft"));
    DeckAircraft->SetupAttachment(ShipRoot);

    HangarInterior = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("HangarInterior"));
    HangarInterior->SetupAttachment(ShipRoot);
    BridgeInterior = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("BridgeInterior"));
    BridgeInterior->SetupAttachment(ShipRoot);
    CICInterior = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("CICInterior"));
    CICInterior->SetupAttachment(ShipRoot);
    EngineeringInterior = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("EngineeringInterior"));
    EngineeringInterior->SetupAttachment(ShipRoot);

    // Import paths are stable targets. Interchange can split GLBs into several meshes, so all
    // components remain editor-assignable if a specific engine build chooses different asset names.
    static ConstructorHelpers::FObjectFinder<UStaticMesh> CompatRef(TEXT("/Game/Enterprise/Compatibility/SM_Enterprise_CV6_1942.SM_Enterprise_CV6_1942"));
    if (CompatRef.Succeeded()) CompatibilityExterior->SetStaticMesh(CompatRef.Object);
    static ConstructorHelpers::FObjectFinder<UStaticMesh> HullRef(TEXT("/Game/Enterprise/Exterior/HullDeck/SM_CV6_HullDeck_Hangar_1942.SM_CV6_HullDeck_Hangar_1942"));
    if (HullRef.Succeeded()) HullDeckHangar->SetStaticMesh(HullRef.Object);
    static ConstructorHelpers::FObjectFinder<UStaticMesh> IslandRef(TEXT("/Game/Enterprise/Exterior/Island/SM_CV6_Island_1942.SM_CV6_Island_1942"));
    if (IslandRef.Succeeded()) IslandExterior->SetStaticMesh(IslandRef.Object);
    static ConstructorHelpers::FObjectFinder<UStaticMesh> WeaponsRef(TEXT("/Game/Enterprise/Exterior/WeaponsFittings/SM_CV6_WeaponsFittings_1942.SM_CV6_WeaponsFittings_1942"));
    if (WeaponsRef.Succeeded()) WeaponsFittings->SetStaticMesh(WeaponsRef.Object);
    static ConstructorHelpers::FObjectFinder<UStaticMesh> AircraftRef(TEXT("/Game/Enterprise/Exterior/DeckAircraft/SM_CV6_DeckAircraft_1942.SM_CV6_DeckAircraft_1942"));
    if (AircraftRef.Succeeded()) DeckAircraft->SetStaticMesh(AircraftRef.Object);

    static ConstructorHelpers::FObjectFinder<UStaticMesh> HangarRef(TEXT("/Game/Enterprise/Interiors/Hangar/SM_CV6_Hangar_1942.SM_CV6_Hangar_1942"));
    if (HangarRef.Succeeded()) HangarInterior->SetStaticMesh(HangarRef.Object);
    static ConstructorHelpers::FObjectFinder<UStaticMesh> BridgeRef(TEXT("/Game/Enterprise/Interiors/Bridge/SM_CV6_Bridge_1942.SM_CV6_Bridge_1942"));
    if (BridgeRef.Succeeded()) BridgeInterior->SetStaticMesh(BridgeRef.Object);
    static ConstructorHelpers::FObjectFinder<UStaticMesh> CICRef(TEXT("/Game/Enterprise/Interiors/CIC/SM_CV6_CIC_1942.SM_CV6_CIC_1942"));
    if (CICRef.Succeeded()) CICInterior->SetStaticMesh(CICRef.Object);
    static ConstructorHelpers::FObjectFinder<UStaticMesh> EngRef(TEXT("/Game/Enterprise/Interiors/Engineering/SM_CV6_Engineering_1942.SM_CV6_Engineering_1942"));
    if (EngRef.Succeeded()) EngineeringInterior->SetStaticMesh(EngRef.Object);

    // Source model uses meters. These reconstruction offsets place local-origin interior modules
    // into the full-ship frame. They remain clearly marked reconstruction until archival CV-6
    // compartment plans are traced room-by-room.
    HangarInterior->SetRelativeLocation(FVector(-100.f, 0.f, 595.f));
    BridgeInterior->SetRelativeLocation(FVector(3500.f, 1165.f, 1555.f));
    CICInterior->SetRelativeLocation(FVector(3200.f, 1165.f, 1325.f));
    EngineeringInterior->SetRelativeLocation(FVector(-500.f, 0.f, 0.f));

    const bool bHasModularHull = HullDeckHangar->GetStaticMesh() != nullptr;
    CompatibilityExterior->SetVisibility(!bHasModularHull, true);
}

void AEnterpriseCV6Actor::BeginPlay()
{
    Super::BeginPlay();
    SetInteriorVisibility(true, true, true, true);
    SetExteriorDetailVisibility(true, true, true);
}

void AEnterpriseCV6Actor::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    if (UGameInstance* GI = GetGameInstance())
    {
        if (UWarSimStateBridge* Bridge = GI->GetSubsystem<UWarSimStateBridge>())
        {
            if (Bridge->bLoadedLegacyCareer)
            {
                FRotator R = GetActorRotation();
                R.Yaw = Bridge->ShipHeadingDeg;
                SetActorRotation(R);
            }
        }
    }
}

void AEnterpriseCV6Actor::SetInteriorVisibility(bool bHangar, bool bBridge, bool bCIC, bool bEngineering)
{
    HangarInterior->SetVisibility(bHangar, true);
    BridgeInterior->SetVisibility(bBridge, true);
    CICInterior->SetVisibility(bCIC, true);
    EngineeringInterior->SetVisibility(bEngineering, true);
}

void AEnterpriseCV6Actor::SetExteriorDetailVisibility(bool bIsland, bool bWeapons, bool bAircraft)
{
    IslandExterior->SetVisibility(bIsland, true);
    WeaponsFittings->SetVisibility(bWeapons, true);
    DeckAircraft->SetVisibility(bAircraft, true);
}
