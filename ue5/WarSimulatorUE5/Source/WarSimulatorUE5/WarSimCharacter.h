#pragma once
#include "CoreMinimal.h"
#include "GameFramework/Character.h"
#include "WarSimCharacter.generated.h"

UCLASS()
class WARSIMULATORUE5_API AWarSimCharacter : public ACharacter
{
    GENERATED_BODY()
public:
    AWarSimCharacter();
    virtual void SetupPlayerInputComponent(UInputComponent* PlayerInputComponent) override;
protected:
    UPROPERTY(VisibleAnywhere) class UCameraComponent* FirstPersonCamera;
    void MoveForward(float Value);
    void MoveRight(float Value);
    void Turn(float Value);
    void LookUp(float Value);
};
