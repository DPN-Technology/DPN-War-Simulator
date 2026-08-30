#pragma once
#include "CoreMinimal.h"
#include "Engine/TriggerBox.h"
#include "CV6CompartmentVolume.generated.h"

UCLASS()
class WARSIMULATORUE5_API ACV6CompartmentVolume : public ATriggerBox
{
    GENERATED_BODY()
public:
    ACV6CompartmentVolume();

    UFUNCTION(BlueprintCallable, Category="War Simulator|Enterprise|Compartment")
    void ApplySimState(float InFloodingPct, float InFireIntensity, float InSmokePct, bool bInPowered);

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="War Simulator|Enterprise|Compartment") FString CompartmentId;
    UPROPERTY(BlueprintReadOnly, Category="War Simulator|Enterprise|Compartment") float FloodingPct = 0.f;
    UPROPERTY(BlueprintReadOnly, Category="War Simulator|Enterprise|Compartment") float FireIntensity = 0.f;
    UPROPERTY(BlueprintReadOnly, Category="War Simulator|Enterprise|Compartment") float SmokePct = 0.f;
    UPROPERTY(BlueprintReadOnly, Category="War Simulator|Enterprise|Compartment") bool bPowered = true;
};
