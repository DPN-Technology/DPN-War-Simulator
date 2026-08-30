#pragma once
#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "CV6WatertightDoorActor.generated.h"

UCLASS()
class WARSIMULATORUE5_API ACV6WatertightDoorActor : public AActor
{
    GENERATED_BODY()
public:
    ACV6WatertightDoorActor();
    virtual void Tick(float DeltaSeconds) override;

    UFUNCTION(BlueprintCallable, Category="War Simulator|Enterprise|Damage Control")
    void ToggleDoor();
    UFUNCTION(BlueprintCallable, Category="War Simulator|Enterprise|Damage Control")
    void SetDoorOpen(bool bOpen);

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="War Simulator|Enterprise|Damage Control") FString BoundaryId;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="War Simulator|Enterprise|Damage Control") bool bLocked = false;
    UPROPERTY(BlueprintReadOnly, Category="War Simulator|Enterprise|Damage Control") bool bIsOpen = false;

protected:
    UPROPERTY(VisibleAnywhere) class USceneComponent* Root;
    UPROPERTY(VisibleAnywhere) class UStaticMeshComponent* FrameMesh;
    UPROPERTY(VisibleAnywhere) class UStaticMeshComponent* DoorMesh;
    UPROPERTY(EditAnywhere) float OpenAngleDeg = 102.f;
    UPROPERTY(EditAnywhere) float OpenSpeedDegPerSec = 120.f;
    float TargetYaw = 0.f;
};
