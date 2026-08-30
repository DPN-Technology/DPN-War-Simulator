#pragma once
#include "CoreMinimal.h"
#include "GameFramework/GameModeBase.h"
#include "WarSimGameMode.generated.h"

UCLASS()
class WARSIMULATORUE5_API AWarSimGameMode : public AGameModeBase
{
    GENERATED_BODY()
public:
    AWarSimGameMode();
    virtual void BeginPlay() override;
};
