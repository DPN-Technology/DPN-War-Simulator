#pragma once
#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "EnterpriseCV6Actor.generated.h"

UCLASS()
class WARSIMULATORUE5_API AEnterpriseCV6Actor : public AActor
{
    GENERATED_BODY()
public:
    AEnterpriseCV6Actor();
    virtual void Tick(float DeltaSeconds) override;

    UFUNCTION(BlueprintCallable, Category="War Simulator|Enterprise")
    void SetInteriorVisibility(bool bHangar, bool bBridge, bool bCIC, bool bEngineering);

    UFUNCTION(BlueprintCallable, Category="War Simulator|Enterprise")
    void SetExteriorDetailVisibility(bool bIsland, bool bWeaponsFittings, bool bDeckAircraft);

protected:
    virtual void BeginPlay() override;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Enterprise|Mesh") class USceneComponent* ShipRoot;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Enterprise|Mesh") class UStaticMeshComponent* CompatibilityExterior;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Enterprise|Mesh") class UStaticMeshComponent* HullDeckHangar;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Enterprise|Mesh") class UStaticMeshComponent* IslandExterior;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Enterprise|Mesh") class UStaticMeshComponent* WeaponsFittings;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Enterprise|Mesh") class UStaticMeshComponent* DeckAircraft;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Enterprise|Mesh") class UStaticMeshComponent* HangarInterior;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Enterprise|Mesh") class UStaticMeshComponent* BridgeInterior;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Enterprise|Mesh") class UStaticMeshComponent* CICInterior;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Enterprise|Mesh") class UStaticMeshComponent* EngineeringInterior;
};
