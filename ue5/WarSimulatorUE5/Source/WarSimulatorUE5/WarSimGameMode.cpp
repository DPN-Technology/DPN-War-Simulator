#include "WarSimGameMode.h"
#include "WarSimCharacter.h"
#include "EnterpriseCV6Actor.h"
#include "Engine/World.h"
#include "Kismet/GameplayStatics.h"

AWarSimGameMode::AWarSimGameMode(){ DefaultPawnClass = AWarSimCharacter::StaticClass(); }
void AWarSimGameMode::BeginPlay()
{
    Super::BeginPlay();
    if(!UGameplayStatics::GetActorOfClass(GetWorld(), AEnterpriseCV6Actor::StaticClass()))
    {
        // GLB uses meters; UE uses centimeters. Imported Interchange scale should be 100.
        GetWorld()->SpawnActor<AEnterpriseCV6Actor>(AEnterpriseCV6Actor::StaticClass(), FVector::ZeroVector, FRotator::ZeroRotator);
    }
}
