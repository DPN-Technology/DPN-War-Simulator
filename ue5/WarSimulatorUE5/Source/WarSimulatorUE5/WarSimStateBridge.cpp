#include "WarSimStateBridge.h"
#include "Dom/JsonObject.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "HAL/PlatformProcess.h"

void UWarSimStateBridge::Initialize(FSubsystemCollectionBase& Collection)
{
    Super::Initialize(Collection);
    ReloadLegacyCareer();
}

bool UWarSimStateBridge::ReloadLegacyCareer()
{
    const FString LocalAppData = FPlatformProcess::UserSettingsDir();
    // Python client stores Windows saves in %LOCALAPPDATA%/WarSimulator/career.json.
    FString Path = FPaths::Combine(LocalAppData, TEXT("WarSimulator"), TEXT("career.json"));
    FString Raw;
    if(!FFileHelper::LoadFileToString(Raw, *Path))
    {
        bLoadedLegacyCareer = false;
        UE_LOG(LogTemp, Log, TEXT("War Simulator bridge: legacy save not found at %s"), *Path);
        return false;
    }
    TSharedPtr<FJsonObject> Root;
    TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(Raw);
    if(!FJsonSerializer::Deserialize(Reader, Root) || !Root.IsValid()) return false;
    const TSharedPtr<FJsonObject>* ProfilePtr=nullptr;
    if(!Root->TryGetObjectField(TEXT("profile"), ProfilePtr) || !ProfilePtr || !ProfilePtr->IsValid()) return false;
    const TSharedPtr<FJsonObject>& P=*ProfilePtr;
    auto Number=[&](const TCHAR* Key, float DefaultValue){ double V=DefaultValue; P->TryGetNumberField(Key,V); return (float)V; };
    PlayerWorldX=Number(TEXT("player_world_x"),0.f);
    PlayerWorldY=Number(TEXT("player_world_y"),0.f);
    PlayerWorldZ=Number(TEXT("player_world_z"),0.f);
    ShipHeadingDeg=Number(TEXT("ship_heading_deg"),90.f);
    ShipSpeedKnots=Number(TEXT("ship_speed_knots"),0.f);
    ShipHullIntegrity=Number(TEXT("ship_hull_integrity"),100.f);
    bLoadedLegacyCareer=true;
    UE_LOG(LogTemp, Log, TEXT("War Simulator bridge: loaded legacy career, ship heading %.1f speed %.1f"), ShipHeadingDeg, ShipSpeedKnots);
    return true;
}
