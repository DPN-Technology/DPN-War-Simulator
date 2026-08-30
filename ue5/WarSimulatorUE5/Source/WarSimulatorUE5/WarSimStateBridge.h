#pragma once
#include "CoreMinimal.h"
#include "Subsystems/GameInstanceSubsystem.h"
#include "WarSimStateBridge.generated.h"

UCLASS()
class WARSIMULATORUE5_API UWarSimStateBridge : public UGameInstanceSubsystem
{
    GENERATED_BODY()
public:
    virtual void Initialize(FSubsystemCollectionBase& Collection) override;
    UFUNCTION(BlueprintCallable, Category="War Simulator|Bridge") bool ReloadLegacyCareer();

    UPROPERTY(BlueprintReadOnly, Category="War Simulator|Bridge") float PlayerWorldX = 0.f;
    UPROPERTY(BlueprintReadOnly, Category="War Simulator|Bridge") float PlayerWorldY = 0.f;
    UPROPERTY(BlueprintReadOnly, Category="War Simulator|Bridge") float PlayerWorldZ = 0.f;
    UPROPERTY(BlueprintReadOnly, Category="War Simulator|Bridge") float ShipHeadingDeg = 90.f;
    UPROPERTY(BlueprintReadOnly, Category="War Simulator|Bridge") float ShipSpeedKnots = 0.f;
    UPROPERTY(BlueprintReadOnly, Category="War Simulator|Bridge") float ShipHullIntegrity = 100.f;
    UPROPERTY(BlueprintReadOnly, Category="War Simulator|Bridge") bool bLoadedLegacyCareer = false;
};
